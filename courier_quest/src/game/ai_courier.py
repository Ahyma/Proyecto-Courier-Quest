# game/ai_courier.py
import random
import time
import heapq
from enum import Enum
from collections import deque  # para historial de posiciones recientes

from game.courier import Courier
from game.pathfinding import find_path


# ==================== DIFICULTAD / IA ====================

class AIDifficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3


class AICourier(Courier):
    """
    IA para Courier Quest.

    - EASY:
        * Camina de forma sencilla (random walk ligero) y se mueve de forma voraz
          hacia el pickup o dropoff del pedido actual.

    - MEDIUM:
        * Usa un lookahead de 2–3 movimientos para escoger el mejor paso
          según una función de puntuación con parámetros α, β, γ, δ, ε.

    - HARD:
        * Usa A* para planear rutas completas hacia pickup/dropoff.
        * Replanifica (A dinámico) cuando cambia el clima o el objetivo.
        * Selecciona trabajos usando una cola de prioridad y una heurística
          tipo TSP aproximado (considera la posible siguiente entrega).

    Además:
        - Hereda de Courier, por lo que la velocidad ya integra Mpeso.
        - Limita su capacidad de carga para que no acepte trabajos imposibles.
    """

    def __init__(self, start_x, start_y, image,
                 difficulty: AIDifficulty, max_weight: int = 6):
        super().__init__(start_x=start_x, start_y=start_y, image=image)
        self.difficulty = difficulty

        # Capacidad de carga específica de la IA
        if hasattr(self, "inventory"):
            self.inventory.max_weight = max_weight
        self.max_weight_ia = max_weight

        # Cooldown entre decisiones de movimiento
        self.move_timer = 0.0

        # Estado del objetivo actual
        self._target_job_id = None        # id del Job objetivo
        self._target_stage = None         # "to_pickup" | "to_dropoff"
        self._target_time = 0.0           # tiempo persiguiendo el mismo job

        # HARD: ruta planificada y clima usado para planear
        self._path = None                 # lista de (x, y)
        self._path_index = 0
        self._last_planned_weather = None

        # Última posición visitada (para EASY) y historial reciente (para MEDIUM/HARD)
        self.last_pos = None
        self.recent_positions = deque(maxlen=6)

        # Estadísticas para análisis técnico
        self.analysis_stats = {
            "frames": 0,
            "time_spent": 0.0,           # tiempo acumulado en update()
            "medium_nodes_evaluated": 0,
            "medium_decisions": 0,
            "hard_replans": 0,
            "job_selections": 0,
        }

    # ---------- DEBUG / INSPECCIÓN ----------

    def get_debug_path(self):
        """
        Devuelve una copia de la ruta planificada actual (solo IA HARD).
        """
        return list(self._path) if self._path else []

    # ---------- UTILIDADES INTERNAS ----------

    def _cooldown_for_difficulty(self) -> float:
        """
        Tiempo entre decisiones de movimiento según dificultad.
        """
        if self.difficulty == AIDifficulty.EASY:
            return 0.35
        if self.difficulty == AIDifficulty.MEDIUM:
            return 0.22
        return 0.16  # HARD

    # ---------- JOB SELECTION / COLA DE PRIORIDAD ----------

    def _evaluate_job_score_medium(self, job, game_world, weather_manager,
                                   current_game_time: float) -> float:
        """
        Heurística para IA MEDIA (un solo job):

            score = α * payout
                    - β * distancia_total
                    - γ * coste_estamina
                    + δ * prioridad
                    - ε * peso_inventario
        """
        # Parámetros (ajustables)
        alpha = 1.1   # importancia del pago
        beta = 0.8    # castigo por distancia
        gamma = 0.4   # castigo por estamina
        delta = 0.3   # premio por prioridad alta
        epsilon = 0.2 # castigo por ir muy cargado

        # Distancias Manhattan aproximadas
        dist_to_pickup = abs(self.x - job.pickup_pos[0]) + abs(self.y - job.pickup_pos[1])
        dist_pickup_to_drop = abs(job.pickup_pos[0] - job.dropoff_pos[0]) + abs(job.pickup_pos[1] - job.dropoff_pos[1])
        total_dist = dist_to_pickup + dist_pickup_to_drop

        stamina_mult = weather_manager.get_stamina_cost_multiplier()

        # Estamina actual integrada al coste efectivo:
        # - stamina_ratio ≈ 1.0 si está llena
        # - stamina_ratio ≈ 0.0 si está vacía
        if self.max_stamina > 0:
            stamina_ratio = self.stamina / self.max_stamina
        else:
            stamina_ratio = 1.0

        # Si la estamina es baja, el "costo efectivo" del job aumenta.
        # Factor entre 1.0 (estamina llena) y 2.0 (estamina en 0).
        stamina_factor = 1.0 + (1.0 - stamina_ratio)

        est_cost = total_dist * stamina_mult * stamina_factor

        prio = getattr(job, "priority", 1)
        priority_value = max(0, 2 - prio)  # prioridad 0 > 1 > 2

        weight_penalty = self.inventory.current_weight

        score = (alpha * job.payout
                - beta * total_dist
                - gamma * est_cost
                + delta * priority_value
                - epsilon * weight_penalty)
        return score
#===================================================================================
    def _tsp_like_score_for_job(self, job, candidates: list) -> float:
        """
        IA DIFÍCIL: estima el valor de hacer este job y luego otro (TSP aprox).

        value ≈ (payout1 - λ * dist1) + best(payout2 - μ * dist2)
        """
        lambda_dist = 0.8
        mu_dist = 0.6

        # Distancia del primer job (desde posición actual)
        dist_to_pickup = abs(self.x - job.pickup_pos[0]) + abs(self.y - job.pickup_pos[1])
        dist_pickup_to_drop = (
            abs(job.pickup_pos[0] - job.dropoff_pos[0]) +
            abs(job.pickup_pos[1] - job.dropoff_pos[1])
        )
        dist1 = dist_to_pickup + dist_pickup_to_drop
        value1 = job.payout - lambda_dist * dist1

        # Mejor "segundo job" desde el dropoff del primero
        best_extra = 0.0
        for other in candidates:
            if other.id == job.id:
                continue

            # desde el dropoff de job hasta el pickup del otro
            dist_drop_to_next_pick = (
                abs(job.dropoff_pos[0] - other.pickup_pos[0]) +
                abs(job.dropoff_pos[1] - other.pickup_pos[1])
            )
            dist_pick_next_drop = (
                abs(other.pickup_pos[0] - other.dropoff_pos[0]) +
                abs(other.pickup_pos[1] - other.dropoff_pos[1])
            )
            dist_next = dist_drop_to_next_pick + dist_pick_next_drop

            extra = other.payout - mu_dist * dist_next
            if extra > best_extra:
                best_extra = extra

        return value1 + best_extra

    def _select_target_job(self, available_jobs, game_world, weather_manager,
                           current_game_time: float):
        """
        Selección del siguiente job según dificultad:

          - EASY: aleatorio
          - MEDIUM: heurística α..ε
          - HARD: heurística TSP-like + cola de prioridad
        """
        if not available_jobs:
            return None

        # EASY: random
        if self.difficulty == AIDifficulty.EASY:
            chosen = random.choice(available_jobs)
            self.analysis_stats["job_selections"] += 1
            return chosen

        # MEDIUM: heurística simple
        if self.difficulty == AIDifficulty.MEDIUM:
            best_job = None
            best_score = float("-inf")
            for j in available_jobs:
                if not self.inventory.can_add_job(j):
                    continue
                s = self._evaluate_job_score_medium(j, game_world, weather_manager, current_game_time)
                if s > best_score:
                    best_score = s
                    best_job = j
            if best_job:
                self.analysis_stats["job_selections"] += 1
            return best_job

        # HARD: usar cola de prioridad con score TSP-like
        heap = []
        for j in available_jobs:
            if not self.inventory.can_add_job(j):
                continue
            s = self._tsp_like_score_for_job(j, available_jobs)
            # max-heap con score negativo para usar heapq
            heapq.heappush(heap, (-s, random.random(), j))

        if not heap:
            return None

        _, _, best_job = heapq.heappop(heap)
        self.analysis_stats["job_selections"] += 1
        return best_job

    # ---------- LÓGICA PRINCIPAL DE ACTUALIZACIÓN ----------

    def update(self, delta_time, game_world, weather_manager,
               jobs_manager=None, current_game_time: float = 0.0):
        """
        Actualización por tick de la IA.
        Recibe también jobs_manager y el tiempo de juego para poder recoger/entregar pedidos.
        """
        start_time = time.perf_counter()

        # Reducir cooldown; si aún no toca moverse, salir
        self.move_timer -= delta_time
        if self.move_timer > 0:
            end_time = time.perf_counter()
            self.analysis_stats["frames"] += 1
            self.analysis_stats["time_spent"] += (end_time - start_time)
            return

        # Resetear cooldown según dificultad
        self.move_timer = self._cooldown_for_difficulty()

        # ----------------------------
        # 1) Resolver objetivo actual
        # ----------------------------
        target_job = None
        if self._target_job_id and jobs_manager:
            for j in jobs_manager.all_jobs:
                if j.id == self._target_job_id:
                    target_job = j
                    break

        # Si hay objetivo actual, acumular tiempo siguiéndolo
        if target_job is not None:
            self._target_time += delta_time
            # Timeout genérico: si pasa demasiado tiempo sin lograrlo, soltarlo
            if self._target_time > 15.0:
                self._target_job_id = None
                self._target_stage = None
                self._path = None
                self._path_index = 0
                self._target_time = 0.0
                target_job = None
        else:
            # Sin objetivo, reiniciar contador
            self._target_time = 0.0

        # Si el job objetivo cambió de estado, descartarlo
        if target_job and target_job.state in ("expired", "delivered", "cancelled"):
            self._target_job_id = None
            self._target_stage = None
            self._path = None
            self._path_index = 0
            self._target_time = 0.0
            target_job = None

        # ----------------------------
        # 2) Elegir nuevo objetivo si no hay
        # ----------------------------
        if not target_job and jobs_manager:
            available = [j for j in jobs_manager.available_jobs
                         if j.state == "available"]

            if available:
                target_job = self._select_target_job(
                    available,
                    game_world,
                    weather_manager,
                    current_game_time
                )

                if target_job:
                    self._target_job_id = target_job.id
                    self._target_stage = "to_pickup"
                    self._target_time = 0.0
                    # Al cambiar de objetivo, invalidar ruta previa (HARD)
                    self._path = None
                    self._path_index = 0

        # ----------------------------
        # 3) Recoger / entregar si procede
        # ----------------------------
        if target_job and jobs_manager:
            # Recoger
            if self._target_stage == "to_pickup":
                if target_job.is_at_pickup((self.x, self.y)):
                    success = jobs_manager.try_pickup_job(
                        target_job.id,
                        (self.x, self.y),
                        self.inventory,
                        current_game_time
                    )
                    if success:
                        self._target_stage = "to_dropoff"
                        self._target_time = 0.0
                        # limpiar ruta para recalcular hacia dropoff
                        self._path = None
                        self._path_index = 0

            # Entregar
            elif self._target_stage == "to_dropoff":
                delivered_job = jobs_manager.try_deliver_job(
                    self.inventory,
                    (self.x, self.y),
                    current_game_time
                )
                if delivered_job:
                    # 💰 Ingresos y reputación de la IA
                    mult = self.get_reputation_multiplier()
                    base_payout = delivered_job.payout * mult
                    self.income += base_payout

                    rep_delta = delivered_job.calculate_reputation_change()
                    self.update_reputation(rep_delta)

                    # pedido terminado; limpiar target
                    self._target_job_id = None
                    self._target_stage = None
                    self._path = None
                    self._path_index = 0
                    self._target_time = 0.0
                    target_job = None

        # ----------------------------
        # 4) Decidir movimiento
        # ----------------------------
        neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        move = None

        if self.difficulty == AIDifficulty.EASY:
            move = self._select_move_easy(target_job, game_world, neighbors)
        elif self.difficulty == AIDifficulty.MEDIUM:
            move = self._select_move_medium(
                target_job, game_world, weather_manager, neighbors,
                depth=3,  # lookahead de 3
                current_game_time=current_game_time
            )
        else:  # HARD
            move = self._decide_move_hard(
                target_job, game_world, weather_manager, neighbors
            )

        if move is not None:
            dx, dy = move
            new_x, new_y = self.x + dx, self.y + dy
            if game_world.is_walkable(new_x, new_y):
                stamina_cost_modifier = weather_manager.get_stamina_cost_multiplier()
                surface_weight = game_world.surface_weight_at(new_x, new_y)
                climate_mult = weather_manager.get_speed_multiplier()

                # Guardar posición previa
                prev_x, prev_y = self.x, self.y

                self.move(
                    dx,
                    dy,
                    stamina_cost_modifier=stamina_cost_modifier,
                    surface_weight=surface_weight,
                    climate_mult=climate_mult,
                    game_world=game_world,
                )

                # Actualizar última posición y historial reciente
                self.last_pos = (prev_x, prev_y)
                self.recent_positions.append((self.x, self.y))

        end_time = time.perf_counter()
        self.analysis_stats["frames"] += 1
        self.analysis_stats["time_spent"] += (end_time - start_time)

    # ---------- MOVIMIENTO EASY ----------

    def _select_move_easy(self, target_job, game_world, neighbors):
        """
        IA EASY:
          - Si no tiene objetivo, camina al azar (priorizando tiles caminables).
          - Si tiene objetivo, se mueve de forma voraz hacia el pickup/dropoff.
        """
        last_pos = self.last_pos

        # Sin objetivo: random walk
        if not target_job:
            random.shuffle(neighbors)
            for dx, dy in neighbors:
                nx, ny = self.x + dx, self.y + dy
                if not game_world.is_walkable(nx, ny):
                    continue
                # Evitar devolvernos al tile anterior si hay más opciones
                if last_pos is not None and (nx, ny) == last_pos:
                    continue
                return (dx, dy)
            # Si no había más opción, permitir volver atrás
            for dx, dy in neighbors:
                nx, ny = self.x + dx, self.y + dy
                if game_world.is_walkable(nx, ny):
                    return (dx, dy)
            return None

        # Con objetivo: greedy hacia pickup o dropoff
        if self._target_stage == "to_dropoff" and self.inventory.current_job is not None:
            goal = target_job.dropoff_pos
        else:
            goal = target_job.pickup_pos

        best_move = None
        best_dist = float("inf")
        random.shuffle(neighbors)
        for dx, dy in neighbors:
            nx, ny = self.x + dx, self.y + dy
            if not game_world.is_walkable(nx, ny):
                continue

            dist = abs(nx - goal[0]) + abs(ny - goal[1])

            # Penalizar ligeramente volver al tile anterior
            if last_pos is not None and (nx, ny) == last_pos:
                dist_eff = dist + 0.5  # penalización suave
            else:
                dist_eff = dist

            if dist_eff < best_dist:
                best_dist = dist_eff
                best_move = (dx, dy)

        # Si nada mejora, intentamos random válido
        if best_move is None:
            return self._select_move_easy(None, game_world, neighbors)
        return best_move

    # ---------- MOVIMIENTO MEDIUM (LOOKAHEAD) ----------

    def _select_move_medium(self, target_job, game_world, weather_manager,
                            neighbors, depth: int = 3,
                            current_game_time: float = 0.0):
        """
        IA MEDIA:
        Lookahead de `depth` pasos con heurística:

            score = α * expected_payout
                    - β * distance_to_goal
                    - γ * stamina_penalty
                    + δ * priority_value
                    - ε * weight_penalty

        Es un "minimax" simplificado con un único agente maximizador
        (no modelamos oponente, solo buscamos el máximo score futuro).
        """
        if not target_job:
            return self._select_move_easy(None, game_world, neighbors)

        last_pos = self.last_pos
        recent_set = set(self.recent_positions)

        # Parámetros (ajustables)
        alpha = 1.2   # fuerza del dinero esperado
        beta = 0.9    # castigo por distancia
        gamma = 0.5   # castigo por gasto de estamina
        delta = 0.4   # premio por prioridad alta
        epsilon = 0.3 # castigo por ir muy cargado

        # Objetivo según etapa
        if self._target_stage == "to_dropoff" and self.inventory.current_job is not None:
            goal_pos = target_job.dropoff_pos
        else:
            goal_pos = target_job.pickup_pos

        def heuristic(x, y, stamina_penalty_accum: float) -> float:
            dist_goal = abs(x - goal_pos[0]) + abs(y - goal_pos[1])
            reached = (x, y) == goal_pos
            expected_payout = target_job.payout if reached else 0.0

            prio = getattr(target_job, "priority", 1)
            priority_value = max(0, 2 - prio)  # prioridad 0 > 1 > 2

            weight_penalty = self.inventory.current_weight

            return (alpha * expected_payout
                    - beta * dist_goal
                    - gamma * stamina_penalty_accum
                    + delta * priority_value
                    - epsilon * weight_penalty)

        local_nodes = 0

        def dfs(x, y, depth_left: int, stamina_penalty_accum: float) -> float:
            nonlocal local_nodes
            local_nodes += 1

            if depth_left == 0:
                return heuristic(x, y, stamina_penalty_accum)

            best_score = float("-inf")
            any_move = False

            for dx, dy in neighbors:
                nx, ny = x + dx, y + dy
                if not game_world.is_walkable(nx, ny):
                    continue

                any_move = True
                stamina_mult = weather_manager.get_stamina_cost_multiplier()
                surface_weight = game_world.surface_weight_at(nx, ny)
                move_cost = stamina_mult * surface_weight

                child_score = dfs(nx, ny, depth_left - 1, stamina_penalty_accum + move_cost)
                if child_score > best_score:
                    best_score = child_score

            if not any_move:
                return heuristic(x, y, stamina_penalty_accum)

            return best_score

        best_move = None
        best_global_score = float("-inf")

        for dx, dy in neighbors:
            nx, ny = self.x + dx, self.y + dy
            if not game_world.is_walkable(nx, ny):
                continue

            stamina_mult = weather_manager.get_stamina_cost_multiplier()
            surface_weight = game_world.surface_weight_at(nx, ny)
            move_cost = stamina_mult * surface_weight

            # Penalizar un poco devolvernos al último tile en el PRIMER paso
            if last_pos is not None and (nx, ny) == last_pos:
                move_cost += 1.0

            # Penalizar más fuerte casillas visitadas muy recientemente
            if (nx, ny) in recent_set:
                move_cost += 2.5

            score = dfs(nx, ny, depth - 1, move_cost)
            if score > best_global_score:
                best_global_score = score
                best_move = (dx, dy)

        self.analysis_stats["medium_nodes_evaluated"] += local_nodes
        self.analysis_stats["medium_decisions"] += 1

        if best_move is None:
            return self._select_move_easy(target_job, game_world, neighbors)
        return best_move

    # ---------- MOVIMIENTO HARD (A* DINÁMICO) ----------

    def _decide_move_hard(self, target_job, game_world, weather_manager, neighbors):
        """
        IA HARD:
          - Usa A* (find_path) para planear ruta completa hacia pickup/dropoff.
          - Replanifica cuando cambia el clima o cambia el objetivo.
        """
        # Sin objetivo, comportarse como MEDIUM (explora hasta que tenga job)
        if not target_job:
            return self._select_move_medium(None, game_world, weather_manager, neighbors)

        # Destino: pickup o dropoff
        if self._target_stage == "to_dropoff" and self.inventory.current_job is not None:
            dest = target_job.dropoff_pos
        else:
            dest = target_job.pickup_pos

        current_weather = weather_manager.get_current_condition()
        need_replan = False

        if self._path is None or self._path_index >= len(self._path) - 1:
            need_replan = True
        elif self._last_planned_weather != current_weather:
            need_replan = True
        elif self.stamina < 0.25 * self.max_stamina:
            # Opcional: replanificar si la estamina está muy baja
            need_replan = True

        if need_replan:
            self.analysis_stats["hard_replans"] += 1
            path = find_path((self.x, self.y), dest, game_world, weather_manager, courier=self)
            self._path = path
            self._path_index = 0
            self._last_planned_weather = current_weather

        # Si no hay ruta válida, mantener el mismo objetivo,
        # pero movernos como MEDIUM hacia él (fallback seguro).
        if not self._path or len(self._path) < 2:
            return self._select_move_medium(target_job, game_world, weather_manager, neighbors)

        # La ruta devuelta incluye la posición actual en el índice 0
        if self._path_index >= len(self._path) - 1:
            return None

        next_pos = self._path[self._path_index + 1]
        nx, ny = next_pos
        dx, dy = nx - self.x, ny - self.y

        # Si el siguiente paso no es transitable, obligamos replanificación en el próximo tick
        if not game_world.is_walkable(nx, ny):
            self._path = None
            self._path_index = 0
            return self._select_move_medium(target_job, game_world, weather_manager, neighbors)

        self._path_index += 1
        return (dx, dy)

    # ---------- ANÁLISIS TÉCNICO ----------

    def get_debug_stats(self) -> dict:
        """
        Devuelve métricas para análisis técnico de la IA:
          - frames: total de llamadas a update()
          - avg_ms_per_update: tiempo promedio por update en ms
          - medium_nodes_evaluated: nodos totales explorados en lookahead
          - medium_avg_nodes: nodos promedio por decisión de IA MEDIA
          - hard_replans: cuántas veces se recalculó el A* (IA HARD)
          - job_selections: cuántas veces eligió un nuevo job
        """
        frames = max(1, self.analysis_stats.get("frames", 1))
        time_spent = self.analysis_stats.get("time_spent", 0.0)
        medium_nodes = self.analysis_stats.get("medium_nodes_evaluated", 0)
        medium_decisions = max(1, self.analysis_stats.get("medium_decisions", 0))

        return {
            "frames": frames,
            "avg_ms_per_update": (time_spent / frames) * 1000.0,
            "medium_nodes_evaluated": medium_nodes,
            "medium_avg_nodes": medium_nodes / medium_decisions,
            "hard_replans": self.analysis_stats.get("hard_replans", 0),
            "job_selections": self.analysis_stats.get("job_selections", 0),
        }
