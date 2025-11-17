# game/ai_courier.py
import random
from enum import Enum

from game.courier import Courier
from game.pathfinding import find_path

# ==================== DIFICULTAD / IA ====================
# Dividir en clases aparte
class AIDifficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3


class AICourier(Courier):
    """
    IA de Courier Quest:

    - EASY:
        * Random walk + movimiento "voraz" hacia el pickup/dropoff.
        * Tiene timeout de objetivo: si pasa mucho tiempo sin lograrlo, suelta el pedido.
    - MEDIUM:
        * Usa una heurística con horizonte pequeño (lookahead) para escoger el mejor movimiento.
        * La función de puntuación combina pago esperado, distancia y penalización por clima.
    - HARD:
        * Usa el pathfinding (find_path) basado en el grafo del mapa y el clima.
        * Replanifica si cambia el clima o la estamina está muy baja.

    Nota importante:
        Hereda de Courier, por lo que su velocidad ya integra Mpeso:
            Mpeso = max(0.8, 1 - 0.03 * peso_total)
        usando el peso actual del inventario.

        Además, la IA tiene su propia capacidad de carga: limitamos el peso total
        en su inventario para que no acepte pedidos que la sobrepasen.
    """

    def __init__(self, start_x, start_y, image, difficulty: AIDifficulty, max_weight: int = 6):
        super().__init__(start_x=start_x, start_y=start_y, image=image)
        self.difficulty = difficulty

        # Capacidad de carga específica de la IA:
        # ajustamos max_weight del inventario sin tocar al jugador humano.
        if hasattr(self, "inventory"):
            self.inventory.max_weight = max_weight
        self.max_weight_ia = max_weight

        # Cada cuánto se puede mover (cooldown de IA)
        self.move_timer = 0.0

        # Targeting / job state para la IA
        self._target_job_id = None         # id del Job objetivo
        self._target_stage = None          # "to_pickup" | "to_dropoff"

        # HARD: plan de ruta (lista de (x,y)) e índice actual
        self._path = None
        self._path_index = 0
        self._last_planned_weather = None

        # Timeout de objetivo: acumula cuánto tiempo lleva persiguiendo el mismo job
        self._target_time = 0.0

    # ---------- MÉTODO DE DEBUG ----------
    def get_debug_path(self):
        """
        Devuelve una copia de la ruta planificada actual (lista de (x, y)).

        Se usa solo para visualización (modo debug). Si no hay ruta, devuelve [].
        """
        if not self._path:
            return []
        return list(self._path)

    def _cooldown_for_difficulty(self) -> float:
        if self.difficulty == AIDifficulty.EASY:
            return 0.6
        if self.difficulty == AIDifficulty.HARD:
            return 0.20
        return 0.35  # MEDIUM

    def update(self, delta_time, game_world, weather_manager,
               jobs_manager=None, current_game_time: float = 0.0):
        """
        Actualización por tick de la IA.
        Recibe también jobs_manager y el tiempo de juego para poder recoger/entregar pedidos.
        """
        # Reducir cooldown; si aún no toca moverse, salir
        self.move_timer -= delta_time
        if self.move_timer > 0:
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

        # Si hay objetivo actual, acumular tiempo persiguiéndolo
        if target_job is not None:
            self._target_time += delta_time
            # Timeout genérico: si pasa demasiado tiempo sin lograr el objetivo, soltarlo
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

        # Si el job objetivo cambió de estado a algo no útil, limpiar objetivo
        if target_job:
            if target_job.state in ("expired", "delivered", "cancelled"):
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
            # Solo considerar pedidos aún disponibles Y que la IA pueda cargar
            available = [
                j for j in jobs_manager.available_jobs
                if j.state == "available" and self.inventory.can_add_job(j)
            ]

            if available:
                if self.difficulty == AIDifficulty.EASY:
                    # Cualquier job disponible
                    target_job = random.choice(available)
                else:
                    # MEDIUM/HARD: heurística simple (payout - 1.5 * distancia)
                    def score_job(j):
                        d = abs(self.x - j.pickup_pos[0]) + abs(self.y - j.pickup_pos[1])
                        return j.payout - 1.5 * d

                    target_job = max(available, key=score_job)

                if target_job:
                    self._target_job_id = target_job.id
                    self._target_stage = "to_pickup"
                    self._target_time = 0.0
                    # Al cambiar de objetivo, invalidar ruta previa (HARD)
                    self._path = None
                    self._path_index = 0

        # ----------------------------
        # 3) Moverse según objetivo
        # ----------------------------
        neighbors = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(neighbors)
        moved = False

        if target_job:
            dest = None
            if self._target_stage == "to_pickup":
                dest = target_job.pickup_pos
            elif self._target_stage == "to_dropoff":
                dest = target_job.dropoff_pos

            if dest:
                # Elegir movimiento dependiendo de la dificultad
                if self.difficulty == AIDifficulty.MEDIUM:
                    # Heurística con horizonte corto
                    choice = self._select_move_medium(
                        target_job, game_world, weather_manager,
                        neighbors, depth=3,
                        current_game_time=current_game_time
                    )
                    dx, dy = choice if choice else (0, 0)

                elif self.difficulty == AIDifficulty.HARD:
                    # Pathfinding con find_path (usa grafo + clima)
                    dx, dy = self._decide_move_hard(dest, game_world, weather_manager)

                else:
                    # EASY: greedy hacia la posición destino
                    dx, dy = self._decide_move_easy_greedy(dest, game_world, neighbors)

                if dx != 0 or dy != 0:
                    new_x, new_y = self.x + dx, self.y + dy
                    stamina_cost_modifier = weather_manager.get_stamina_cost_multiplier()
                    climate_mult = weather_manager.get_speed_multiplier()
                    surface_weight = game_world.surface_weight_at(new_x, new_y)

                    self.move(
                        dx,
                        dy,
                        stamina_cost_modifier=stamina_cost_modifier,
                        surface_weight=surface_weight,
                        climate_mult=climate_mult,
                        game_world=game_world,
                    )

                    # Si seguimos un path de HARD, avanzar el índice
                    if self.difficulty == AIDifficulty.HARD and self._path:
                        if self._path_index < len(self._path):
                            next_pos = self._path[self._path_index]
                            if (self.x, self.y) == next_pos:
                                self._path_index += 1

                    moved = True

                    # Intentar recoger/entregar si estamos en pickup/dropoff
                    if self._target_stage == "to_pickup":
                        if target_job.is_at_pickup((self.x, self.y)) and jobs_manager:
                            success = jobs_manager.try_pickup_job(
                                target_job.id, (self.x, self.y),
                                self.inventory, current_game_time
                            )
                            if success:
                                # Cambiar a fase de entrega
                                self._target_stage = "to_dropoff"
                                self._target_time = 0.0
                                # limpiar ruta para recalcular hacia dropoff
                                self._path = None
                                self._path_index = 0
                            else:
                                # Si no se pudo (expiró o sobrepeso), liberar objetivo
                                if target_job.is_expired(current_game_time) or not self.inventory.can_add_job(target_job):
                                    self._target_job_id = None
                                    self._target_stage = None
                                    self._path = None
                                    self._path_index = 0
                                    self._target_time = 0.0

                    elif self._target_stage == "to_dropoff":
                        if (not self.inventory.is_empty()
                                and self.inventory.current_job
                                and self.inventory.current_job.is_at_dropoff((self.x, self.y))
                                and jobs_manager):
                            delivered_job = jobs_manager.try_deliver_job(
                                self.inventory, (self.x, self.y), current_game_time
                            )
                            if delivered_job:
                                # 💰 Ingresos y reputación de la IA (compite contra el jugador)
                                mult = self.get_reputation_multiplier()
                                base_payout = delivered_job.payout * mult
                                self.income += base_payout

                                rep_delta = delivered_job.calculate_reputation_change()
                                self.update_reputation(rep_delta)

                                # Objetivo completado
                                self._target_job_id = None
                                self._target_stage = None
                                self._path = None
                                self._path_index = 0
                                self._target_time = 0.0

        # ----------------------------
        # 4) Si no nos movimos hacia objetivo → random walk
        # ----------------------------
        if not moved:
            for dx, dy in neighbors:
                new_x, new_y = self.x + dx, self.y + dy
                if not game_world.is_walkable(new_x, new_y):
                    continue

                stamina_cost_modifier = weather_manager.get_stamina_cost_multiplier()
                climate_mult = weather_manager.get_speed_multiplier()
                surface_weight = game_world.surface_weight_at(new_x, new_y)

                self.move(
                    dx,
                    dy,
                    stamina_cost_modifier=stamina_cost_modifier,
                    surface_weight=surface_weight,
                    climate_mult=climate_mult,
                    game_world=game_world,
                )
                moved = True
                break

    # ---------------- HELPER EASY ----------------
    def _decide_move_easy_greedy(self, dest, game_world, neighbors):
        """Para EASY: elegir vecino que más acerque en distancia Manhattan, evitando edificios."""
        best = None
        best_dist = abs(self.x - dest[0]) + abs(self.y - dest[1])
        for ndx, ndy in neighbors:
            nx, ny = self.x + ndx, self.y + ndy
            if not game_world.is_walkable(nx, ny):
                continue
            d = abs(nx - dest[0]) + abs(ny - dest[1])
            if d < best_dist:
                best_dist = d
                best = (ndx, ndy)
        return best if best else (0, 0)

    # ---------------- HELPER HARD ----------------
    def _decide_move_hard(self, dest, game_world, weather_manager):
        """
        Para HARD: usa find_path (grafo + clima).
        Replanifica si:
          - No hay path,
          - Cambió el clima,
          - La estamina está muy baja.
        """
        need_replan = False
        current_weather = weather_manager.get_current_condition()

        if self._path is None:
            need_replan = True
        if self._last_planned_weather != current_weather:
            need_replan = True
        if hasattr(self, 'stamina') and self.stamina < (0.25 * max(1, getattr(self, 'max_stamina', 100))):
            need_replan = True

        if need_replan:
            plan_goal = dest
            path = find_path((self.x, self.y), plan_goal, game_world, weather_manager, courier=self)
            self._path = path
            self._path_index = 0
            self._last_planned_weather = current_weather

        if self._path:
            if self._path_index >= len(self._path):
                return (0, 0)
            nx, ny = self._path[self._path_index]
            if not game_world.is_walkable(nx, ny):
                # Si se bloqueó el siguiente tile, forzar replanning en el próximo tick
                self._path = None
                return (0, 0)
            return (nx - self.x, ny - self.y)

        # Fallback: comportamiento EASY si no hay ruta
        return self._decide_move_easy_greedy(dest, game_world, [(1, 0), (-1, 0), (0, 1), (0, -1)])

    # ---------------- MEDIUM ----------------
    def _select_move_medium(self, target_job, game_world, weather_manager,
                            neighbors, depth: int = 3, current_game_time: float = 0.0):
        """
        Lookahead de `depth` pasos con heurística:
            score = α * expected_payout - β * distance_cost - γ * weather_penalty

        (Uso de estructuras más "teóricas" para el modo medio).
        """
        if not target_job:
            return None

        alpha = 1.0
        beta = 1.0
        gamma = 20.0

        def simulate_move_path(start_x, start_y, seq):
            x, y = start_x, start_y
            total_stamina_pen = 0.0
            for dx, dy in seq:
                nx, ny = x + dx, y + dy
                if not game_world.is_walkable(nx, ny):
                    return None
                total_stamina_pen += weather_manager.get_stamina_cost_multiplier()
                x, y = nx, ny
            return x, y, total_stamina_pen

        best_move = None
        best_score = float('-inf')

        for first in neighbors:
            sequences = [[first]]
            for _ in range(1, depth):
                new_seqs = []
                for seq in sequences:
                    for nb in neighbors:
                        new_seqs.append(seq + [nb])
                sequences.extend(new_seqs)

            worst_seq_score = float('-inf')
            valid_found = False
            for seq in sequences:
                res = simulate_move_path(self.x, self.y, seq)
                if res is None:
                    continue
                valid_found = True
                fx, fy, stamina_pen = res

                reached_pickup = False
                tx, ty = self.x, self.y
                for dx, dy in seq:
                    tx += dx
                    ty += dy
                    if target_job.is_at_pickup((tx, ty)):
                        reached_pickup = True
                        break

                expected_payout = target_job.payout if reached_pickup else 0.0
                distance_cost = abs(fx - target_job.pickup_pos[0]) + abs(fy - target_job.pickup_pos[1])
                weather_penalty = stamina_pen

                score = alpha * expected_payout - beta * distance_cost - gamma * weather_penalty
                if score > worst_seq_score:
                    worst_seq_score = score

            if not valid_found:
                continue

            if worst_seq_score > best_score:
                best_score = worst_seq_score
                best_move = first

        return best_move
