import pygame
import sys
import os
import random
from enum import Enum
from datetime import datetime

from api.client import APIClient
from api.cache import APICache
from game.courier import Courier
from game.world import World
from game.constants import TILE_SIZE, PANEL_WIDTH
from game.weather_manager import WeatherManager
from game.pathfinding import find_path
from game.weather_visuals import WeatherVisuals
from game.save_game import save_slot, load_slot
from game.score_board import save_score, load_scores
from game.hud import HUD
from game.jobs_manager import JobsManager
from game.reputation import ReputationSystem  # ⬅️ deltas de reputación
from game.notifications import NotificationsOverlay  # ⬅️ Overlay de notificaciones

# 🔧 RUTAS ABSOLUTAS PARA LAS IMÁGENES
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")


# ==================== DIFICULTAD / IA SENCILLA ====================

class AIDifficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3


class AICourier(Courier):
    """
    IA muy simple: se mueve aleatoriamente por el mapa.
    La dificultad solo cambia qué tan rápido intenta moverse.
    No toca pedidos (solo es un segundo jugador visible).
    """
    def __init__(self, start_x, start_y, image, difficulty: AIDifficulty):
        super().__init__(start_x=start_x, start_y=start_y, image=image)
        self.difficulty = difficulty
        self.move_timer = 0.0
        # Targeting / job state for the AI
        self._target_job_id = None  # id del Job objetivo
        self._target_stage = None  # "to_pickup" | "to_dropoff"
        # HARD-specific: planned path (list of (x,y) positions), and index into it
        self._path = None
        self._path_index = 0
        self._last_planned_weather = None

    def _cooldown_for_difficulty(self) -> float:
        if self.difficulty == AIDifficulty.EASY:
            return 0.6
        if self.difficulty == AIDifficulty.HARD:
            return 0.20
        return 0.35  # MEDIUM

    def update(self, delta_time, game_world, weather_manager, jobs_manager=None, current_game_time: float = 0.0):
        self.move_timer -= delta_time
        if self.move_timer > 0:
            return

        # Nuevo cooldown
        self.move_timer = self._cooldown_for_difficulty()

        # Elegir un movimiento aleatorio
        # Si hay un objetivo de trabajo, intentar gestionarlo (pickup / delivery)
        target_job = None
        if self._target_job_id and jobs_manager:
            # Buscar referencia del job en all_jobs
            for j in jobs_manager.all_jobs:
                if j.id == self._target_job_id:
                    target_job = j
                    break

        # Si no hay objetivo válido, seleccionar uno según dificultad
        if not target_job and jobs_manager:
            available = [j for j in jobs_manager.available_jobs if j.state == "available"]
            if available:
                if self.difficulty == AIDifficulty.EASY:
                    target_job = random.choice(available)
                else:
                    # MEDIUM: heurística simple, HARD fallback to highest payout
                    def score_job(j):
                        # distancia manhattan desde la posición actual hasta pickup
                        d = abs(self.x - j.pickup_pos[0]) + abs(self.y - j.pickup_pos[1])
                        return j.payout - 1.5 * d

                    target_job = max(available, key=score_job)

                if target_job:
                    self._target_job_id = target_job.id
                    self._target_stage = "to_pickup"

        # Si tenemos objetivo y está en estado 'available' o 'picked_up', intentar acercarnos
        if target_job:
            # Si ya fue recogido por otro, limpiar objetivo
            if target_job.state == "expired" or target_job.state == "delivered" or target_job.state == "cancelled":
                self._target_job_id = None
                self._target_stage = None
                target_job = None

        # Movimiento simple: vecino aleatorio que sea transitable
        neighbors = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(neighbors)
        moved = False

        # Si hay un target, priorizar mover hacia él (pickup o dropoff según stage)
        if target_job:
            dest = None
            if self._target_stage == "to_pickup":
                dest = target_job.pickup_pos
            elif self._target_stage == "to_dropoff":
                dest = target_job.dropoff_pos

            if dest:
                # Si MEDIUM, usar lookahead para elegir mejor movimiento; en EASY usar vecino y en HARD usar A* pathfinding
                # manhattan es la suma de las diferencias absolutas de sus coordenadas, usada para medir distancia en cuadrícula. 
                if self.difficulty == AIDifficulty.MEDIUM:
                    # elegir movimiento mediante lookahead
                    choice = self._select_move_medium(target_job, game_world, weather_manager, neighbors, depth=3, current_game_time=current_game_time)
                    if choice:
                        dx, dy = choice
                    else:
                        dx, dy = 0, 0
                else:
                    if self.difficulty == AIDifficulty.HARD:
                        # Replan si no hay path o si cambió el clima o si la estamina es baja
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

                        # If we have a path, follow next step
                        if self._path:
                            # validate next step
                            if self._path_index >= len(self._path):
                                # already at goal (or path consumed) -> no movement
                                dx, dy = 0, 0
                            else:
                                nx, ny = self._path[self._path_index]
                                # If next tile became non-walkable, force replan next tick
                                if not game_world.is_walkable(nx, ny):
                                    self._path = None
                                    dx, dy = 0, 0
                                else:
                                    dx, dy = nx - self.x, ny - self.y
                                    # advance index after performing move (below)
                        else:
                            # fallback to greedy neighbor if no path found
                            best = None
                            best_dist = abs(self.x - dest[0]) + abs(self.y - dest[1])
                            for dx, dy in neighbors:
                                nx, ny = self.x + dx, self.y + dy
                                if not game_world.is_walkable(nx, ny):
                                    continue
                                d = abs(nx - dest[0]) + abs(ny - dest[1])
                                if d < best_dist:
                                    best_dist = d
                                    best = (dx, dy)

                            if best:
                                dx, dy = best

                # si dx,dy es 0,0 significa no se eligió movimiento válido
                if dx == 0 and dy == 0:
                    pass
                else:
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
                    # If following a planned path, advance the index
                    if self.difficulty == AIDifficulty.HARD and self._path:
                        # If the move matched the planned next tile, advance
                        if self._path_index < len(self._path):
                            next_pos = self._path[self._path_index]
                            if (self.x, self.y) == next_pos:
                                self._path_index += 1
                    moved = True

                    # Si estamos en pickup/dropoff, intentar acción
                    if self._target_stage == "to_pickup":
                        # comprobación distancia para pickup (is_at_pickup usa distancia Manhattan ≤1)
                        if target_job.is_at_pickup((self.x, self.y)) and jobs_manager:
                            success = jobs_manager.try_pickup_job(target_job.id, (self.x, self.y), self.inventory, current_game_time)
                            if success:
                                # cambiar a entregar
                                self._target_stage = "to_dropoff"
                            else:
                                # si falló porque expiró o no pudo añadirse, limpiar
                                if target_job.is_expired(current_game_time) or not self.inventory.can_add_job(target_job):
                                    self._target_job_id = None
                                    self._target_stage = None

                    elif self._target_stage == "to_dropoff":
                        if self.inventory.current_job and self.inventory.current_job.is_at_dropoff((self.x, self.y)) and jobs_manager:
                            delivered = jobs_manager.try_deliver_job(self.inventory, (self.x, self.y), current_game_time)
                            if delivered:
                                # cobro y reputación son gestionados por main loop; limpiamos objetivo
                                self._target_job_id = None
                                self._target_stage = None

        

        # Si no movimos hacia target, hacer movimiento aleatorio válido
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

        if not moved:
            return

    def _select_move_medium(self, target_job, game_world, weather_manager, neighbors, depth: int = 3, current_game_time: float = 0.0):
        """Busca mediante lookahead de `depth` el movimiento (dx,dy) que maximiza
        una función heurística simple:
            score = alpha * expected_payout - beta * distance_cost - gamma * weather_penalty

        Para simplificar, `expected_payout` se cuenta si en el horizonte se alcanza el pickup;
        `distance_cost` es la distancia restante hasta pickup; `weather_penalty` usa multiplicador de stamina.
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
                    return None  # path invalid
                # approximate stamina penalty by current weather stamina multiplier
                total_stamina_pen += weather_manager.get_stamina_cost_multiplier()
                x, y = nx, ny
            return x, y, total_stamina_pen

        best_move = None
        best_score = float('-inf')

        # Evaluate each first-step neighbor by enumerating all sequences up to depth
        for first in neighbors:
            # build list of sequences starting with `first`
            sequences = [[first]]
            for d in range(1, depth):
                new_seqs = []
                for seq in sequences:
                    last_x, last_y = self.x, self.y
                    for dx, dy in seq:
                        last_x += dx
                        last_y += dy
                    for nb in neighbors:
                        new_seq = seq + [nb]
                        new_seqs.append(new_seq)
                sequences.extend(new_seqs)

            # evaluate sequences (but only need final pos for heuristic)
            worst_seq_score = float('-inf')
            valid_found = False
            for seq in sequences:
                res = simulate_move_path(self.x, self.y, seq)
                if res is None:
                    continue
                valid_found = True
                fx, fy, stamina_pen = res

                # Check if pickup would be reachable at any step in this seq
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

            # the score for the first move is the best over sequences that start with it
            if worst_seq_score > best_score:
                best_score = worst_seq_score
                best_move = first

        return best_move


# ==================== MENÚ PRINCIPAL ====================

class Menu:
    """
    Menú principal tipo:
      Courier Quest II
      [Dificultad IA: ...]
      [Nueva partida]
      [Cargar partida]
      [Puntuaciones]
      [Salir]
    """

    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        pygame.font.init()
        self.title_font = pygame.font.SysFont("arial", 64, bold=True)
        self.button_font = pygame.font.SysFont("arial", 32, bold=True)

        self.buttons = []
        self._build_buttons()

    def _build_buttons(self):
        center_x = self.width // 2
        start_y = self.height // 2 - 140
        button_width = 360
        button_height = 56
        margin = 20

        labels_actions = [
            ("Dificultad IA", "toggle_difficulty"),
            ("Nueva Partida", "new_game"),
            ("Cargar Partida", "load_game"),
            ("Puntuaciones", "show_scores"),
            ("Salir", "exit"),
        ]

        self.buttons = []
        for i, (label, action) in enumerate(labels_actions):
            x = center_x - button_width // 2
            y = start_y + i * (button_height + margin)
            rect = pygame.Rect(x, y, button_width, button_height)
            self.buttons.append({"rect": rect, "label": label, "action": action})

    @staticmethod
    def _difficulty_to_text(diff: AIDifficulty) -> str:
        if diff == AIDifficulty.EASY:
            return "EASY"
        if diff == AIDifficulty.HARD:
            return "HARD"
        return "MEDIUM"

    @staticmethod
    def _next_difficulty(diff: AIDifficulty) -> AIDifficulty:
        if diff == AIDifficulty.EASY:
            return AIDifficulty.MEDIUM
        if diff == AIDifficulty.MEDIUM:
            return AIDifficulty.HARD
        return AIDifficulty.EASY

    def show(self, current_difficulty: AIDifficulty):
        """
        Bucle del menú.
        Devuelve (action, difficulty).
        """
        clock = pygame.time.Clock()
        running = True
        difficulty = current_difficulty

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit", difficulty
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    for btn in self.buttons:
                        if btn["rect"].collidepoint(mx, my):
                            if btn["action"] == "toggle_difficulty":
                                difficulty = self._next_difficulty(difficulty)
                            else:
                                return btn["action"], difficulty

            # Fondo gris
            self.screen.fill((200, 200, 200))

            # Título
            title_surface = self.title_font.render("Courier Quest II", True, (0, 0, 0))
            title_rect = title_surface.get_rect(center=(self.width // 2, 120))
            self.screen.blit(title_surface, title_rect)

            # Botones
            for btn in self.buttons:
                rect = btn["rect"]
                color = (60, 60, 60)
                if btn["action"] == "exit":
                    color = (200, 0, 0)

                pygame.draw.rect(self.screen, color, rect, border_radius=6)

                if btn["action"] == "toggle_difficulty":
                    text = f"Dificultad IA: {self._difficulty_to_text(difficulty)}"
                else:
                    text = btn["label"]

                text_surf = self.button_font.render(text, True, (255, 255, 255))
                text_rect = text_surf.get_rect(center=rect.center)
                self.screen.blit(text_surf, text_rect)

            pygame.display.flip()
            clock.tick(60)

        return None, difficulty


# ==================== CARGA DE IMÁGENES ====================

def load_building_images():
    """Carga y devuelve un diccionario de imágenes de edificios por su tamaño."""
    building_images = {}
    image_names = {
        (3, 8): "edificio3x8.png",
        (5, 5): "edificio4x6.png",
        (6, 5): "edificio4x5.png",
        (7, 6): "edificio5x7.png",
        (7, 8): "edificio6x8.png",
        (8, 9): "edificio7x9.png",
    }

    base_path = IMAGES_DIR

    for size, filename in image_names.items():
        image_path = os.path.join(base_path, filename)
        try:
            image = pygame.image.load(image_path).convert_alpha()
            building_images[size] = image
            print(f"Imagen de edificio {filename} ({size}) cargada con éxito desde: {image_path}")
        except (pygame.error, FileNotFoundError) as e:
            print(f"[AVISO] No se pudo cargar la imagen de edificio {filename} desde {image_path}: {e}")
            print("        Se usará color de fallback para ese tamaño de edificio.")
            building_images[size] = None

    return building_images


def load_street_images():
    """Carga la imagen única del patrón de calle (calle.png)."""
    base_path = IMAGES_DIR
    street_images = {}

    filename = "calle.png"
    image_path = os.path.join(base_path, filename)

    try:
        image = pygame.image.load(image_path).convert_alpha()
        street_images["patron_base"] = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
        print(f"Imagen {filename} cargada con éxito desde: {image_path}")
    except (pygame.error, FileNotFoundError) as e:
        print(f"[AVISO] No se pudo cargar la imagen de calle {filename} desde {image_path}: {e}")
        print("        Se usará color de fallback para las calles.")
        street_images["patron_base"] = None

    return street_images


# ==================== PARTIDA (JUEGO) ====================

def start_game(ai_difficulty: AIDifficulty, load_saved: bool = False):
    # Inicialización de Pygame
    pygame.init()

    # API + Cache
    api_cache = APICache()
    api_client = APIClient(api_cache)

    # Carga de datos
    map_data = api_client.get_map_data()
    jobs_data = api_client.get_jobs_data()
    weather_data = api_client.get_weather_data()

    if not map_data:
        print("Error CRÍTICO: No se pudo cargar los datos del mapa. Saliendo.")
        pygame.quit()
        sys.exit()

    # Info de mapa
    map_info = map_data.get("data", {})
    game_start_time = datetime.fromisoformat(map_info.get("start_time", "2025-09-01T12:00:00Z"))
    jobs_manager = JobsManager(jobs_data, game_start_time)

    # Tamaño pantalla dinámico
    map_tile_width = map_info.get("width", 20)
    map_tile_height = map_info.get("height", 15)
    SCREEN_WIDTH = map_tile_width * TILE_SIZE
    SCREEN_HEIGHT = map_tile_height * TILE_SIZE

    # Ventana
    screen_size = (SCREEN_WIDTH + PANEL_WIDTH, SCREEN_HEIGHT)
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("Courier Quest - En Juego")

    # Reloj
    clock = pygame.time.Clock()
    FPS = 60

    # Imágenes
    building_images = load_building_images()
    street_images = load_street_images()

    # Césped
    try:
        cesped_path = os.path.join(IMAGES_DIR, "cesped.png")
        cesped_image = pygame.image.load(cesped_path).convert_alpha()
        cesped_image = pygame.transform.scale(cesped_image, (TILE_SIZE, TILE_SIZE))
    except (pygame.error, FileNotFoundError) as e:
        print(f"[AVISO] No se pudo cargar la imagen del césped desde {cesped_path}: {e}")
        print("        Se usará color de fallback para el césped.")
        cesped_image = None

    # Repartidor (imagen compartida humano + IA)
    try:
        repartidor_path = os.path.join(IMAGES_DIR, "repartidor.png")
        repartidor_image = pygame.image.load(repartidor_path).convert_alpha()
        repartidor_image = pygame.transform.scale(repartidor_image, (TILE_SIZE, TILE_SIZE))
    except (pygame.error, FileNotFoundError) as e:
        print(f"[AVISO] No se pudo cargar la imagen del repartidor desde {repartidor_path}: {e}")
        print("        Se usará un fallback para el repartidor.")
        repartidor_image = None

    # Mundo y sistemas
    game_world = World(
        map_data=map_data,
        building_images=building_images,
        grass_image=cesped_image,
        street_images=street_images,
    )
    courier = Courier(start_x=0, start_y=0, image=repartidor_image)

    # IA colocada en la esquina opuesta
    ai_courier = AICourier(
        start_x=map_tile_width - 1,
        start_y=map_tile_height - 1,
        image=repartidor_image,
        difficulty=ai_difficulty,
    )

    weather_manager = WeatherManager(weather_data)
    weather_visuals = WeatherVisuals((SCREEN_WIDTH, SCREEN_HEIGHT), TILE_SIZE)

    # HUD
    hud_area = pygame.Rect(SCREEN_WIDTH, 0, PANEL_WIDTH, SCREEN_HEIGHT)
    hud = HUD(hud_area, SCREEN_HEIGHT, TILE_SIZE)

    # Overlay de notificaciones
    notifier = NotificationsOverlay(panel_width=PANEL_WIDTH, screen_height=SCREEN_HEIGHT)

    # Generar pedidos si no hay JSON
    if not jobs_data or not jobs_data.get("data"):
        print("📦 Forzando generación de nuevos pedidos...")
        jobs_manager.generate_random_jobs(game_world, num_jobs=10)

        print("🔍 VERIFICANDO PEDIDOS GENERADOS:")
        print(f"   Total de pedidos: {len(jobs_manager.all_jobs)}")
        print(f"   Pedidos disponibles: {len(jobs_manager.available_jobs)}")
        for i, job in enumerate(jobs_manager.all_jobs):
            print(f"   {i+1}. {job.id} - Pos: {job.pickup_pos} - Release: {job.release_time}s - Estado: {job.state}")
    else:
        print("📦 Usando pedidos del JSON")
        print("🔍 VERIFICANDO PEDIDOS DEL JSON:")
        print(f"   Total de pedidos: {len(jobs_manager.all_jobs)}")
        print(f"   Pedidos disponibles: {len(jobs_manager.available_jobs)}")

    # Tiempo/meta
    elapsed_time = 0.0
    max_time = map_info.get("max_time", 900)  # s
    goal_income = map_info.get("goal", 0)

    # Si se pidió cargar partida
    if load_saved:
        try:
            loaded_data = load_slot("slot1.sav")
            if loaded_data:
                courier.load_state(loaded_data.get("courier", {}))
                elapsed_time = loaded_data.get("elapsed_time", 0.0)
                print("📂 Partida cargada desde slot1.sav (solo jugador humano).")
                notifier.success("Partida cargada")
            else:
                print("Archivo de guardado vacío o corrupto.")
                notifier.error("Guardado vacío o corrupto")
        except FileNotFoundError:
            print("No se encontró 'slot1.sav'. Se inicia nueva partida.")
            notifier.error("No existe 'slot1.sav', se inicia nueva partida")

    # Bucle principal
    running = True
    while running:
        delta_time = clock.tick(FPS) / 1000.0
        elapsed_time += delta_time
        remaining_time = max_time - elapsed_time

        # Condiciones fin de juego
        if remaining_time <= 0:
            print("Game Over: se acabó el tiempo.")
            final_score = courier.income * (1.05 if courier.reputation >= 90 else 1.0)
            save_score({
                "score": round(final_score, 2),
                "income": round(courier.income, 2),
                "time": round(elapsed_time, 2),
                "reputation": int(courier.reputation),
            })
            notifier.error("Tiempo agotado — partida guardada")
            running = False

        if courier.reputation < 20 and running:
            print("Game Over: reputación muy baja.")
            final_score = courier.income * (1.05 if courier.reputation >= 90 else 1.0)
            save_score({
                "score": round(final_score, 2),
                "income": round(courier.income, 2),
                "time": round(elapsed_time, 2),
                "reputation": int(courier.reputation),
            })
            notifier.error("Derrota: reputación < 20 — partida guardada")
            running = False

        if courier.income >= goal_income and goal_income > 0 and running:
            print("¡Victoria! Meta alcanzada.")
            final_score = courier.income
            if courier.reputation >= 90:
                final_score *= 1.05  # Bono por reputación alta
            save_score({
                "score": round(final_score, 2),
                "income": round(courier.income, 2),
                "time": round(elapsed_time, 2),
                "reputation": int(courier.reputation),
            })
            notifier.success("¡Meta alcanzada! Score guardado")
            running = False

        courier_pos = (courier.x, courier.y)
        jobs_manager.update(elapsed_time, courier_pos)
        weather_manager.update(delta_time)

        # Actualizar IA (se mueve sola) — ahora con acceso a jobs_manager y tiempo de juego
        ai_courier.update(delta_time, game_world, weather_manager, jobs_manager, elapsed_time)

        # Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                dx, dy = 0, 0
                if event.key == pygame.K_UP:
                    dy = -1
                elif event.key == pygame.K_DOWN:
                    dy = 1
                elif event.key == pygame.K_LEFT:
                    dx = -1
                elif event.key == pygame.K_RIGHT:
                    dx = 1

                # --- Pedidos (jugador humano) ---
                elif event.key == pygame.K_SPACE:  # Recoger
                    try:
                        nearby_jobs = jobs_manager.get_available_jobs_nearby(courier_pos, max_distance=1)
                        pickup_success = False
                        for job in nearby_jobs:
                            if job.is_at_pickup(courier_pos):
                                if jobs_manager.try_pickup_job(job.id, courier_pos, courier.inventory, elapsed_time):
                                    print(f"✅ Pedido {job.id} recogido! +${job.payout}")
                                    notifier.success(f"Pedido {job.id} recogido (+${job.payout:.0f})")
                                    pickup_success = True
                                    break
                        if not pickup_success:
                            print("❌ No hay pedidos para recoger desde esta posición")
                            notifier.warn("No hay pedidos para recoger aquí")
                    except Exception as e:
                        print(f"Error en recogida: {e}")
                        notifier.error("Error al recoger")

                elif event.key == pygame.K_e:  # Entregar
                    if not courier.inventory.is_empty():
                        _before = courier.inventory.current_job
                        delivered_job = jobs_manager.try_deliver_job(courier.inventory, courier_pos, elapsed_time)

                        if delivered_job:
                            mult = courier.get_reputation_multiplier()
                            base_payout = delivered_job.payout * mult
                            if mult > 1.0:
                                print("💰 ¡Bono de reputación aplicado! +5%")
                                notifier.info("Bono +5% por reputación ≥90")

                            courier.income += base_payout

                            reputation_change = delivered_job.calculate_reputation_change()
                            new_rep_below_20 = courier.update_reputation(reputation_change)
                            if reputation_change != 0:
                                signo = "+" if reputation_change > 0 else ""
                                print(f"⭐ Reputación {signo}{reputation_change} (total: {courier.reputation})")
                                col = (120, 255, 120) if reputation_change > 0 else (255, 160, 160)
                                notifier.add(f"Reputación {signo}{reputation_change} (total {courier.reputation})", color=col)

                            print(f"🎉 Pedido {delivered_job.id} entregado! +${base_payout:.0f}")
                            notifier.success(f"Entregado {delivered_job.id} (+${base_payout:.0f})")

                            if new_rep_below_20:
                                print("Game Over: reputación muy baja.")
                                final_score = courier.income * (1.05 if courier.reputation >= 90 else 1.0)
                                save_score({
                                    "score": round(final_score, 2),
                                    "income": round(courier.income, 2),
                                    "time": round(elapsed_time, 2),
                                    "reputation": int(courier.reputation),
                                })
                                notifier.error("Derrota: reputación < 20 — partida guardada")
                                running = False
                        else:
                            if _before and _before.state == "expired":
                                delta = ReputationSystem.for_delivery(
                                    res=type("R", (), {"status": "expired"})()
                                )
                                new_rep_below_20 = courier.update_reputation(delta)
                                print("⛔ Pedido expirado en inventario. Reputación -6 (total: {})".format(courier.reputation))
                                notifier.error("Pedido expirado en inventario (-6 rep)")
                                if new_rep_below_20:
                                    print("Game Over: reputación muy baja.")
                                    final_score = courier.income * (1.05 if courier.reputation >= 90 else 1.0)
                                    save_score({
                                        "score": round(final_score, 2),
                                        "income": round(courier.income, 2),
                                        "time": round(elapsed_time, 2),
                                        "reputation": int(courier.reputation),
                                    })
                                    notifier.error("Derrota: reputación < 20 — partida guardada")
                                    running = False
                            else:
                                print("❌ No estás en posición de entrega")
                                notifier.warn("No estás en el dropoff")
                    else:
                        print("❌ No tienes pedidos para entregar")
                        notifier.warn("Inventario vacío")

                elif event.key == pygame.K_TAB:  # Navegar inventario
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        courier.inventory.previous_job()
                        print("Pedido anterior seleccionado")
                        notifier.info("Pedido anterior")
                    else:
                        courier.inventory.next_job()
                        print("Siguiente pedido seleccionado")
                        notifier.info("Siguiente pedido")

                elif event.key == pygame.K_c:  # Cancelar pedido actual
                    current_job = courier.inventory.current_job
                    if current_job and current_job.cancel():
                        cancelled_job = courier.inventory.remove_current_job()
                        delta = ReputationSystem.for_cancel()  # -4
                        new_rep_below_20 = courier.update_reputation(delta)
                        print(f"⚠️ Pedido {cancelled_job.id} cancelado. Reputación {delta} (total: {courier.reputation})")
                        notifier.warn(f"Cancelado {cancelled_job.id} ({delta} rep)")
                        if new_rep_below_20:
                            print("Game Over: reputación muy baja.")
                            final_score = courier.income * (1.05 if courier.reputation >= 90 else 1.0)
                            save_score({
                                "score": round(final_score, 2),
                                "income": round(courier.income, 2),
                                "time": round(elapsed_time, 2),
                                "reputation": int(courier.reputation),
                            })
                            notifier.error("Derrota: reputación < 20 — partida guardada")
                            running = False

                # Ordenamiento inventario
                elif event.key == pygame.K_F1:  # Prioridad
                    if not courier.inventory.is_empty():
                        courier.inventory.apply_sort("priority")
                        print("📊 Inventario reordenado por PRIORIDAD")
                        notifier.info("Ordenado por PRIORIDAD")
                elif event.key == pygame.K_F2:  # Deadline
                    if not courier.inventory.is_empty():
                        courier.inventory.apply_sort("deadline", current_game_time=elapsed_time)
                        print("⏰ Inventario reordenado por DEADLINE")
                        notifier.info("Ordenado por DEADLINE")
                elif event.key == pygame.K_F3:  # Pago
                    if not courier.inventory.is_empty():
                        courier.inventory.apply_sort("payout")
                        print("💰 Inventario reordenado por PAGO")
                        notifier.info("Ordenado por PAGO")
                elif event.key == pygame.K_F4:  # Original
                    if not courier.inventory.is_empty():
                        courier.inventory.apply_sort("original")
                        print("🔄 Orden ORIGINAL restaurada")
                        notifier.info("Orden ORIGINAL")

                # Guardado/Carga
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    data_to_save = {"courier": courier.get_save_state(), "elapsed_time": elapsed_time}
                    save_slot("slot1.sav", data_to_save)
                    print("💾 Partida guardada.")
                    notifier.success("Partida guardada")

                elif event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    try:
                        loaded_data = load_slot("slot1.sav")
                        if loaded_data:
                            courier.load_state(loaded_data.get("courier", {}))
                            elapsed_time = loaded_data.get("elapsed_time", 0.0)
                            print("📂 Partida cargada.")
                            notifier.success("Partida cargada")
                        else:
                            print("Archivo de guardado vacío o corrupto.")
                            notifier.error("Guardado vacío o corrupto")
                    except FileNotFoundError:
                        print("No se encontró 'slot1.sav'.")
                        notifier.error("No existe 'slot1.sav'")

                # Movimiento (aplica clima y coste de estamina/superficie)
                if dx != 0 or dy != 0:
                    stamina_cost_modifier = weather_manager.get_stamina_cost_multiplier()
                    climate_mult = weather_manager.get_speed_multiplier()
                    new_x, new_y = courier.x + dx, courier.y + dy

                    if game_world.is_walkable(new_x, new_y):
                        surface_weight = game_world.surface_weight_at(new_x, new_y)
                        courier.move(
                            dx,
                            dy,
                            stamina_cost_modifier=stamina_cost_modifier,
                            surface_weight=surface_weight,
                            climate_mult=climate_mult,
                            game_world=game_world,
                        )

        # ---------- RENDER ----------
        screen.fill((0, 0, 0))
        game_world.draw(screen)
        jobs_manager.draw_job_markers(screen, TILE_SIZE, courier_pos)

        # Jugador humano
        courier.draw(screen, TILE_SIZE)
        # IA
        ai_courier.draw(screen, TILE_SIZE)

        # Clima
        current_condition = weather_manager.get_current_condition()
        current_intensity = weather_manager.get_current_intensity()
        weather_visuals.update(delta_time, current_condition, current_intensity)
        weather_visuals.draw(screen)

        # Flags HUD (pickup/entrega cercanos, adyacencia ortogonal)
        near_pickup = False
        near_dropoff = False
        if not courier.inventory.is_empty():
            job = courier.inventory.current_job
            if job:
                if abs(courier.x - job.pickup_pos[0]) + abs(courier.y - job.pickup_pos[1]) == 1:
                    near_pickup = True
                if abs(courier.x - job.dropoff_pos[0]) + abs(courier.y - job.dropoff_pos[1]) == 1:
                    near_dropoff = True

        # HUD (solo muestra datos del jugador humano; la IA es "visual")
        current_speed_mult = weather_manager.get_speed_multiplier()
        hud.draw(
            screen,
            courier,
            current_condition,
            current_speed_mult,
            remaining_time,
            goal_income,
            near_pickup,
            near_dropoff,
            current_game_time=elapsed_time,
            ai_courier=ai_courier
        )

        notifier.update(delta_time)
        notifier.draw(screen, hud_area)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


# ==================== MAIN: MENÚ + PARTIDA ====================

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Courier Quest")

    menu = Menu(screen)
    ai_difficulty = AIDifficulty.MEDIUM

    running = True
    while running:
        action, ai_difficulty = menu.show(ai_difficulty)

        if action == "exit" or action is None:
            running = False

        elif action == "show_scores":
            scores = load_scores()
            print("=== PUNTUACIONES ===")
            for idx, s in enumerate(scores, start=1):
                print(f"{idx}. Score={s['score']} Income={s['income']} Time={s['time']} Rep={s['reputation']}")
            input("Presiona ENTER para volver al menú...")

        elif action == "new_game":
            # Reiniciamos display para que start_game configure la ventana grande
            pygame.display.quit()
            pygame.display.init()
            start_game(ai_difficulty, load_saved=False)
            # Al terminar la partida, volvemos a crear la ventanita del menú
            screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption("Courier Quest")
            menu = Menu(screen)

        elif action == "load_game":
            pygame.display.quit()
            pygame.display.init()
            start_game(ai_difficulty, load_saved=True)
            screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption("Courier Quest")
            menu = Menu(screen)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
