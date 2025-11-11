import pygame
import sys
import os
from datetime import datetime
import random 

from api.client import APIClient
from api.cache import APICache
from game.courier import Courier
from game.world import World
from game.constants import TILE_SIZE, PANEL_WIDTH
from game.weather_manager import WeatherManager
from game.weather_visuals import WeatherVisuals
from game.save_game import save_slot, load_slot
from game.score_board import save_score, load_scores
from game.hud import HUD
from game.jobs_manager import JobsManager
from game.reputation import ReputationSystem
from game.notifications import NotificationsOverlay
from game.undo import UndoStack
from game.menu import MainMenu 
from game.ai_courier import AIDifficulty, AI_Courier # Importar la enumeración y la clase IA
from game.graph_map import GraphMap      
from game.ai_strategy import EasyStrategy, MediumStrategy, HardStrategy




# ------------------ CARGA DE IMÁGENES ------------------
def load_building_images():
    """
    Carga las imágenes de los edificios desde archivos y las escala según el tamaño.
    Retorna un diccionario donde la clave es el tamaño (ancho, alto) y el valor es la imagen.
    """
    building_images = {}
    image_names = {
        (3, 8): "edificio3x8.png",
        (5, 5): "edificio4x6.png",
        (6, 5): "edificio4x5.png",
        (7, 6): "edificio5x7.png",
        (7, 8): "edificio6x8.png",
        (8, 9): "edificio7x9.png",
    }

    base_path = "images"
    for size, filename in image_names.items():
        try:
            # Intenta cargar y escalar la imagen
            image = pygame.image.load(os.path.join(base_path, filename)).convert_alpha()
            building_images[size] = image
            print(f"Imagen de edificio {filename} ({size}) cargada con éxito.")
        except pygame.error as e:
            print(f"Error al cargar imagen de edificio {filename}: {e}. Se usará color de fallback.")
            building_images[size] = None
    return building_images


def load_street_images():
    """
    Carga la imagen de las calles y la escala al tamaño de tile.
    Retorna un diccionario con el patrón base de las calles.
    """
    base_path = "images"
    street_images = {}

    filename = "calle.png"
    try:
        image = pygame.image.load(os.path.join(base_path, filename)).convert_alpha()
        street_images["patron_base"] = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
        print(f"Imagen {filename} cargada con éxito.")
    except pygame.error as e:
        print(f"Error CRÍTICO al cargar imagen de calle {filename}: {e}. Se usará color de fallback.")
        street_images["patron_base"] = None
    return street_images

def create_save_state(courier, ai_courier, elapsed_time, weather_manager):
    """Crea un diccionario con el estado completo del juego para la pila de "deshacer"."""
    return {
        "courier": courier.get_save_state(), 
        "ai_courier": ai_courier.get_save_state(),
        "elapsed_time": elapsed_time,
        "weather_condition": getattr(weather_manager, "current_condition", None),
        "weather_intensity": getattr(weather_manager, "current_intensity", None),
    }


# ------------------ FUNCIÓN DEL JUEGO PRINCIPAL ------------------
def start_game(action, ai_difficulty):
    """
    Función principal que inicia y ejecuta el juego.
    Maneja la inicialización, el bucle principal y la lógica del juego.
    
    Args:
        action: Indica si es "new_game" o "load_game"
    """
    # Inicialización de API y caché
    api_cache = APICache()
    api_client = APIClient(api_cache)

    # Carga de datos del juego
    map_data = api_client.get_map_data()
    jobs_data = api_client.get_jobs_data()
    weather_data = api_client.get_weather_data()

    # Verificación crítica de datos del mapa
    if not map_data:
        print("Error CRÍTICO: No se pudo cargar los datos del mapa. Saliendo.")
        pygame.quit()
        sys.exit()

    # Configuración inicial del juego
    map_info = map_data.get("data", {})
    game_start_time = datetime.fromisoformat(map_info.get("start_time", "2025-09-01T12:00:00Z"))
    jobs_manager = JobsManager(jobs_data, game_start_time)

    # Cálculo dinámico del tamaño de pantalla basado en el mapa
    map_tile_width = map_info.get("width", 20)
    map_tile_height = map_info.get("height", 15)
    SCREEN_WIDTH = map_tile_width * TILE_SIZE
    SCREEN_HEIGHT = map_tile_height * TILE_SIZE

    # Crear ventana del juego
    screen_size = (SCREEN_WIDTH + PANEL_WIDTH, SCREEN_HEIGHT)
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("Courier Quest - En Juego")

    # Configuración de tiempo y FPS
    clock = pygame.time.Clock()
    FPS = 60

    # Carga de recursos gráficos
    building_images = load_building_images()
    street_images = load_street_images()

    # Carga de imagen de césped
    try:
        cesped_image = pygame.image.load(os.path.join("images", "cesped.png")).convert_alpha()
        cesped_image = pygame.transform.scale(cesped_image, (TILE_SIZE, TILE_SIZE))
    except pygame.error as e:
        print(f"Error al cargar la imagen del césped: {e}")
        cesped_image = None

    # Carga de imagen del repartidor JUGADOR
    try:
        repartidor_image = pygame.image.load(os.path.join("images", "repartidor.png")).convert_alpha()
        repartidor_image = pygame.transform.scale(repartidor_image, (TILE_SIZE, TILE_SIZE))
    except pygame.error as e:
        print(f"Error al cargar la imagen del repartidor: {e}")
        repartidor_image = None
        
    # --- INICIO MODIFICACIÓN IA: Carga de imagen del AI Courier ---
    # Carga de imagen del repartidor IA (usando fallback si no existe 'repartidor_ia.png')
    try:
        ai_courier_image = pygame.image.load(os.path.join("images", "repartidorIA.png")).convert_alpha()
        ai_courier_image = pygame.transform.scale(ai_courier_image, (TILE_SIZE, TILE_SIZE))
    except pygame.error as e:
        print(f"Error al cargar la imagen del repartidor IA: {e}. Usando imagen de jugador como fallback.")
        ai_courier_image = repartidor_image # Fallback
    # --- FIN MODIFICACIÓN IA ---

    # Creación de objetos del juego
    game_world = World(
        map_data=map_data,
        building_images=building_images,
        grass_image=cesped_image,
        street_images=street_images,
    )
    
    # Repartidor JUGADOR (posición inicial por defecto 0,0)
    courier = Courier(start_x=0, start_y=0, image=repartidor_image)

    weather_manager = WeatherManager(weather_data)
    weather_visuals = WeatherVisuals((SCREEN_WIDTH, SCREEN_HEIGHT), TILE_SIZE)

    # ------------------ INICIO MODIFICACIÓN IA: Inicialización ------------------

    # 1. Creación del motor de rutas (GraphMap)
    game_graph = GraphMap(game_world) 
    game_world.weather_manager = weather_manager # Asignar WeatherManager al World para acceso desde GraphMap

    # 2. Creación de la instancia del repartidor IA (jugador CPU)
    ai_start_x = map_tile_width - 2 # Usamos -2 para evitar el borde, si es un edificio
    ai_start_y = map_tile_height - 2 # Usamos -2 para evitar el borde, si es un edificio
    ai_courier_start_pos = (ai_start_x, ai_start_y) 

    ai_courier = AI_Courier(
        start_x=ai_courier_start_pos[0],
        start_y=ai_courier_start_pos[1],
        image=ai_courier_image,
        difficulty=ai_difficulty, 
        graph_map=game_graph 
    )

    # --- NUEVA LÓGICA DE ASIGNACIÓN DE ESTRATEGIA (Patrón Strategy) ---
    strategy_instance = None
    if ai_difficulty == AIDifficulty.EASY:
        strategy_instance = EasyStrategy()
    elif ai_difficulty == AIDifficulty.MEDIUM:
        strategy_instance = MediumStrategy()
    elif ai_difficulty == AIDifficulty.HARD:
        strategy_instance = HardStrategy()
        
    if strategy_instance:
        ai_courier.set_strategy(strategy_instance)
    # -----------------------------------------------------------------

    # 3. Registrar el Courier de la IA en JobsManager para que reciba pedidos
    jobs_manager.register_ai_courier(ai_courier) 

    # 4. Reajustar la posición del jugador humano (mantenemos su lógica)
    courier.x = map_tile_width - 1
    courier.y = map_tile_height - 1
    # ------------------ FIN MODIFICACIÓN IA: Inicialización ------------------


    # Configuración de HUD (Heads-Up Display)
    hud_area = pygame.Rect(SCREEN_WIDTH, 0, PANEL_WIDTH, SCREEN_HEIGHT)
    hud = HUD(hud_area, SCREEN_HEIGHT, TILE_SIZE)

    notifier = NotificationsOverlay(panel_width=PANEL_WIDTH, screen_height=SCREEN_HEIGHT)
    undo_stack = UndoStack(limit=20)

    def save_game_state():
        """
        Guarda el estado actual del juego para poder deshacer acciones.
        Incluye posición, estadísticas del repartidor y estado del clima.
        """
        game_state = {
            "courier": {
                "x": courier.x,
                "y": courier.y,
                "stamina": courier.stamina,
                "income": courier.income,
                "reputation": courier.reputation,
                "packages_delivered": courier.packages_delivered,
                "_clean_streak": courier._clean_streak,
            },
            # --- INICIO MODIFICACIÓN IA: Guardar estado de la IA ---
            "ai_courier": {
                "x": ai_courier.x,
                "y": ai_courier.y,
                "stamina": ai_courier.stamina,
                "income": ai_courier.income,
                "reputation": ai_courier.reputation,
                "packages_delivered": ai_courier.packages_delivered,
                "_clean_streak": ai_courier._clean_streak,
            },
            # --- FIN MODIFICACIÓN IA ---
            "elapsed_time": elapsed_time,
            "weather_condition": weather_manager.current_condition,
            "weather_intensity": weather_manager.current_intensity,
        }
        undo_stack.push(game_state)

    def calculate_final_score(courier, elapsed_time, max_time, goal_income):
        """
        Calcula el puntaje final considerando bonos y penalizaciones.
        
        Args:
            courier: Objeto del repartidor con sus estadísticas
            elapsed_time: Tiempo transcurrido en la partida
            max_time: Tiempo máximo permitido
            goal_income: Meta de ingresos a alcanzar
            
        Returns:
            Tupla con score final y detalles de bonos/penalizaciones
        """
        score_base = courier.income
        
        # Bono por reputación alta
        reputation_bonus = 0
        if courier.reputation >= 90:
            reputation_bonus = score_base * 0.05
            score_base += reputation_bonus
        
        # Bono por tiempo restante
        time_bonus = 0
        remaining_time = max_time - elapsed_time
        if remaining_time > (max_time * 0.2) and courier.income >= goal_income:
            time_bonus = remaining_time * 0.1
            print(f"⏰ Bonus por tiempo: +${time_bonus:.0f}")
        
        cancellation_penalty = 0
        
        # Cálculo del score final
        final_score = score_base + time_bonus - cancellation_penalty
        return max(0, final_score), time_bonus, reputation_bonus, cancellation_penalty

    # Generación de pedidos si no hay datos disponibles
    if not jobs_data or not jobs_data.get("data"):
        print("📦 Forzando generación de nuevos pedidos...")
        jobs_manager.generate_random_jobs(game_world, num_jobs=10)

        # Verificación de pedidos generados
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

    # Configuración de temporizadores y metas
    movement_timer = 0.0
    elapsed_time = 0.0
    max_time = map_info.get("max_time", 900)
    goal_income = map_info.get("goal", 0)

    # Carga de partida si se seleccionó desde el menú
    if action == "load_game":
        try:
            loaded_data = load_slot("slot1.sav")
            if loaded_data:
                courier.load_state(loaded_data.get("courier", {}))
                
                # --- INICIO MODIFICACIÓN IA: Carga de estado de la IA ---
                ai_courier.load_state(loaded_data.get("ai_courier", {}))
                # --- FIN MODIFICACIÓN IA ---
                
                elapsed_time = loaded_data.get("elapsed_time", 0.0)
                print("📂 Partida cargada desde el menú.")
                notifier.success("Partida cargada")
            else:
                print("Archivo de guardado vacío o corrupto.")
                notifier.error("Guardado vacío o corrupto")
        except FileNotFoundError:
            print("No se encontró 'slot1.sav'.")
            notifier.error("No existe partida guardada")

    # BUCLE PRINCIPAL DEL JUEGO
    running = True

    # Configuración de movimiento continuo con teclado
    keys_pressed = {
        pygame.K_UP: False,
        pygame.K_DOWN: False,
        pygame.K_LEFT: False,
        pygame.K_RIGHT: False
    }
    move_cooldown = 0.0
    MOVE_COOLDOWN_TIME = 0.1

    while running:
        # Actualización del tiempo del juego
        delta_time = clock.tick(FPS) / 1000.0
        elapsed_time += delta_time
        remaining_time = max_time - elapsed_time

        # Verificación de tipo de tile actual para recuperación de stamina
        current_tile_type = game_world.tiles[courier.y][courier.x] if (0 <= courier.y < game_world.height and 0 <= courier.x < game_world.width) else "C"
        is_resting_spot = (current_tile_type == "P")
        
        courier.recover_stamina(delta_time, is_resting_spot)

        # CONDICIONES DE FIN DE JUEGO
        
        # Tiempo agotado
        if remaining_time <= 0:
            print("Game Over: se acabó el tiempo.")
            final_score, time_bonus, reputation_bonus, penalties = calculate_final_score(courier, elapsed_time, max_time, goal_income)
            save_score({
                "score": round(final_score, 2),
                "income": round(courier.income, 2),
                "time": round(elapsed_time, 2),
                "reputation": int(courier.reputation),
                "time_bonus": round(time_bonus, 2),
                "reputation_bonus": round(reputation_bonus, 2),
                "penalties": round(penalties, 2)
            })
            notifier.error("Tiempo agotado — partida guardada")
            running = False

        # Reputación muy baja
        if courier.reputation < 20 and running:
            print("Game Over: reputación muy baja.")
            final_score, time_bonus, reputation_bonus, penalties = calculate_final_score(courier, elapsed_time, max_time, goal_income)
            save_score({
                "score": round(final_score, 2),
                "income": round(courier.income, 2),
                "time": round(elapsed_time, 2),
                "reputation": int(courier.reputation),
                "time_bonus": round(time_bonus, 2),
                "reputation_bonus": round(reputation_bonus, 2),
                "penalties": round(penalties, 2)
            })
            notifier.error("Derrota: reputación < 20 — partida guardada")
            running = False

        # Meta alcanzada (victoria)
        if courier.income >= goal_income and goal_income > 0 and running:
            print("¡Victoria! Meta alcanzada.")
            
            final_score, time_bonus, reputation_bonus, penalties = calculate_final_score(courier, elapsed_time, max_time, goal_income)
            
            # Mostrar desglose del score
            print(f"💰 Score base: ${courier.income:.0f}")
            if reputation_bonus > 0:
                print(f"⭐ Bonus reputación: +${reputation_bonus:.0f}")
            if time_bonus > 0:
                print(f"⏰ Bonus tiempo: +${time_bonus:.0f}")
            if penalties > 0:
                print(f"⚠️  Penalizaciones: -${penalties:.0f}")
            print(f"🏆 Score final: ${final_score:.0f}")
            
            # Guardar score
            save_score({
                "score": round(final_score, 2),
                "income": round(courier.income, 2),
                "time": round(elapsed_time, 2),
                "reputation": int(courier.reputation),
                "time_bonus": round(time_bonus, 2),
                "reputation_bonus": round(reputation_bonus, 2),
                "penalties": round(penalties, 2)
            })
            notifier.success("¡Meta alcanzada! Score guardado")
            running = False

        # MANEJO DE EVENTOS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # Movimiento con teclas direccionales
                if event.key in keys_pressed:
                    keys_pressed[event.key] = True
                    
                # Deshacer acción (Ctrl+Z)
                elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    saved_state = undo_stack.pop()
                    if saved_state:
                        # Restaurar estado anterior del juego
                        courier.x = saved_state["courier"]["x"]
                        courier.y = saved_state["courier"]["y"]
                        courier.stamina = saved_state["courier"]["stamina"]
                        courier.income = saved_state["courier"]["income"]
                        courier.reputation = saved_state["courier"]["reputation"]
                        courier.packages_delivered = saved_state["courier"]["packages_delivered"]
                        courier._clean_streak = saved_state["courier"]["_clean_streak"]
                        
                        # --- INICIO MODIFICACIÓN IA: Restaurar estado de la IA ---
                        ai_courier.x = saved_state["ai_courier"]["x"]
                        ai_courier.y = saved_state["ai_courier"]["y"]
                        ai_courier.stamina = saved_state["ai_courier"]["stamina"]
                        ai_courier.income = saved_state["ai_courier"]["income"]
                        ai_courier.reputation = saved_state["ai_courier"]["reputation"]
                        ai_courier.packages_delivered = saved_state["ai_courier"]["packages_delivered"]
                        ai_courier._clean_streak = saved_state["ai_courier"]["_clean_streak"]
                        # --- FIN MODIFICACIÓN IA ---
                        
                        elapsed_time = saved_state["elapsed_time"]
                        
                        weather_manager.current_condition = saved_state["weather_condition"]
                        weather_manager.current_intensity = saved_state["weather_intensity"]
                        
                        print("↩️  Deshecho último movimiento")
                        notifier.info("Deshecho último movimiento")
                    else:
                        print("❌ No hay acciones para deshacer")
                        notifier.warn("No hay acciones para deshacer")

                # Recoger pedido (ESPACIO)
                elif event.key == pygame.K_SPACE:
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

                # Entregar pedido (E)
                elif event.key == pygame.K_e:
                    if not courier.inventory.is_empty():
                        _before = courier.inventory.current_job
                        delivered_job = jobs_manager.try_deliver_job(courier.inventory, courier_pos, elapsed_time)

                        if delivered_job:
                            # Aplicar multiplicador de reputación al pago
                            mult = courier.get_reputation_multiplier()
                            base_payout = delivered_job.payout * mult
                            if mult > 1.0:
                                print("💰 ¡Bono de reputación aplicado! +5%")
                                notifier.info("Bono +5% por reputación ≥90")

                            courier.income += base_payout

                            # Actualizar reputación según puntualidad
                            reputation_change = delivered_job.calculate_reputation_change()
                            new_rep_below_20 = courier.update_reputation(reputation_change)
                            if reputation_change != 0:
                                signo = "+" if reputation_change > 0 else ""
                                print(f"⭐ Reputación {signo}{reputation_change} (total: {courier.reputation})")
                                col = (120, 255, 120) if reputation_change > 0 else (255, 160, 160)
                                notifier.add(f"Reputación {signo}{reputation_change} (total {courier.reputation})", color=col)

                            print(f"🎉 Pedido {delivered_job.id} entregado! +${base_payout:.0f}")
                            notifier.success(f"Entregado {delivered_job.id} (+${base_payout:.0f})")

                            # Verificar si la reputación cayó demasiado después de la entrega
                            if new_rep_below_20:
                                print("Game Over: reputación muy baja.")
                                final_score, time_bonus, reputation_bonus, penalties = calculate_final_score(courier, elapsed_time, max_time, goal_income)
                                save_score({
                                    "score": round(final_score, 2),
                                    "income": round(courier.income, 2),
                                    "time": round(elapsed_time, 2),
                                    "reputation": int(courier.reputation),
                                    "time_bonus": round(time_bonus, 2),
                                    "reputation_bonus": round(reputation_bonus, 2),
                                    "penalties": round(penalties, 2)
                                })
                                notifier.error("Derrota: reputación < 20 — partida guardada")
                                running = False
                        else:
                            # Manejar pedido expirado en inventario
                            if _before and _before.state == "expired":
                                delta = ReputationSystem.for_delivery(
                                    res=type("R", (), {"status": "expired"})()
                                )
                                new_rep_below_20 = courier.update_reputation(delta)
                                print("⛔ Pedido expirado en inventario. Reputación -6 (total: {})".format(courier.reputation))
                                notifier.error("Pedido expirado en inventario (-6 rep)")
                                if new_rep_below_20:
                                    print("Game Over: reputación muy baja.")
                                    final_score, time_bonus, reputation_bonus, penalties = calculate_final_score(courier, elapsed_time, max_time, goal_income)
                                    save_score({
                                        "score": round(final_score, 2),
                                        "income": round(courier.income, 2),
                                        "time": round(elapsed_time, 2),
                                        "reputation": int(courier.reputation),
                                        "time_bonus": round(time_bonus, 2),
                                        "reputation_bonus": round(reputation_bonus, 2),
                                        "penalties": round(penalties, 2)
                                    })
                                    notifier.error("Derrota: reputación < 20 — partida guardada")
                                    running = False
                            else:
                                print("❌ No estás en posición de entrega")
                                notifier.warn("No estás en el dropoff")
                    else:
                        print("❌ No tienes pedidos para entregar")
                        notifier.warn("Inventario vacío")

                # Cambiar entre pedidos en inventario (TAB)
                elif event.key == pygame.K_TAB:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        courier.inventory.previous_job()
                        print("Pedido anterior seleccionado")
                        notifier.info("Pedido anterior")
                    else:
                        courier.inventory.next_job()
                        print("Siguiente pedido seleccionado")
                        notifier.info("Siguiente pedido")

                # Cancelar pedido actual (C)
                elif event.key == pygame.K_c:
                    current_job = courier.inventory.current_job
                    if current_job and current_job.cancel():
                        cancelled_job = courier.inventory.remove_current_job()
                        delta = ReputationSystem.for_cancel()
                        new_rep_below_20 = courier.update_reputation(delta)
                        print(f"⚠️ Pedido {cancelled_job.id} cancelado. Reputación {delta} (total: {courier.reputation})")
                        notifier.warn(f"Cancelado {cancelled_job.id} ({delta} rep)")
                        if new_rep_below_20:
                            print("Game Over: reputación muy baja.")
                            final_score, time_bonus, reputation_bonus, penalties = calculate_final_score(courier, elapsed_time, max_time, goal_income)
                            save_score({
                                "score": round(final_score, 2),
                                "income": round(courier.income, 2),
                                "time": round(elapsed_time, 2),
                                "reputation": int(courier.reputation),
                                "time_bonus": round(time_bonus, 2),
                                "reputation_bonus": round(reputation_bonus, 2),
                                "penalties": round(penalties, 2)
                            })
                            notifier.error("Derrota: reputación < 20 — partida guardada")
                            running = False

                # Listar pedidos cercanos (A)
                elif event.key == pygame.K_a:
                    try:
                        nearby = jobs_manager.get_available_jobs_nearby(courier_pos, max_distance=3)
                        if not nearby:
                            print("🔎 No hay pedidos cercanos (≤3 celdas).")
                            notifier.info("No hay pedidos cercanos (≤3)")
                        else:
                            print(f"🔎 Pedidos cercanos ({len(nearby)}):")
                            for j in nearby:
                                tl = None
                                if hasattr(j, "get_time_until_deadline"):
                                    try:
                                        tl = int(j.get_time_until_deadline(elapsed_time))
                                    except Exception:
                                        tl = None
                                tl_txt = f" | TTL: {tl}s" if tl is not None else ""
                                print(f"   - {j.id} @ {j.pickup_pos} → {j.dropoff_pos} | $ {j.payout} | prio {getattr(j,'priority',0)}{tl_txt}")
                            notifier.info(f"{len(nearby)} pedidos cercanos listados en consola")
                    except Exception as e:
                        print(f"Error al listar pedidos cercanos: {e}")
                        notifier.error("Error listando pedidos cercanos")

                # ORDENAMIENTO DE INVENTARIO
                elif event.key == pygame.K_F1:
                    if not courier.inventory.is_empty():
                        courier.inventory.apply_sort("priority")
                        print("📊 Inventario reordenado por PRIORIDAD")
                        notifier.info("Ordenado por PRIORIDAD")
                elif event.key == pygame.K_F2:
                    if not courier.inventory.is_empty():
                        courier.inventory.apply_sort("deadline", current_game_time=elapsed_time)
                        print("⏰ Inventario reordenado por DEADLINE")
                        notifier.info("Ordenado por DEADLINE")
                elif event.key == pygame.K_F3:
                    if not courier.inventory.is_empty():
                        courier.inventory.apply_sort("payout")
                        print("💰 Inventario reordenado por PAGO")
                        notifier.info("Ordenado por PAGO")
                elif event.key == pygame.K_F4:
                    if not courier.inventory.is_empty():
                        courier.inventory.apply_sort("original")
                        print("🔄 Orden ORIGINAL restaurada")
                        notifier.info("Orden ORIGINAL")

                # Guardar partida (Ctrl+S)
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    # --- INICIO MODIFICACIÓN IA: Incluir datos de la IA al guardar ---
                    data_to_save = {
                        "courier": courier.get_save_state(), 
                        "ai_courier": ai_courier.get_save_state(),
                        "elapsed_time": elapsed_time
                    }
                    # --- FIN MODIFICACIÓN IA ---
                    save_slot("slot1.sav", data_to_save)
                    print("💾 Partida guardada.")
                    notifier.success("Partida guardada")

                # Cargar partida (Ctrl+L)
                elif event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    try:
                        loaded_data = load_slot("slot1.sav")
                        if loaded_data:
                            courier.load_state(loaded_data.get("courier", {}))
                            # --- INICIO MODIFICACIÓN IA: Cargar datos de la IA ---
                            ai_courier.load_state(loaded_data.get("ai_courier", {}))
                            # --- FIN MODIFICACIÓN IA ---
                            elapsed_time = loaded_data.get("elapsed_time", 0.0)
                            print("📂 Partida cargada.")
                            notifier.success("Partida cargada")
                        else:
                            print("Archivo de guardado vacío o corrupto.")
                            notifier.error("Guardado vacío o corrupto")
                    except FileNotFoundError:
                        print("No se encontró 'slot1.sav'.")
                        notifier.error("No existe 'slot1.sav'")

            # Liberar teclas de movimiento
            elif event.type == pygame.KEYUP:
                if event.key in keys_pressed:
                    keys_pressed[event.key] = False

        # MOVIMIENTO CONTINUO DEL REPARTIDOR JUGADOR
        dx, dy = 0, 0

        # Sincronización de Movimiento del Jugador
        movement_timer += delta_time
        move_delay = courier.get_time_per_tile(game_world, weather_manager)

        if movement_timer >= move_delay:
            
            if keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_RIGHT]:
                
                # Guarda estado antes del movimiento (usa la función recién definida)
                current_state = create_save_state(courier, ai_courier, elapsed_time, weather_manager)
                if current_state:
                    undo_stack.push(current_state)
                
                # Reinicia el temporizador
                movement_timer = 0.0 
                
                # Ejecuta el movimiento
                if keys_pressed[pygame.K_UP]:
                    courier.move(0, -1, game_world, jobs_manager) 
                elif keys_pressed[pygame.K_DOWN]:
                    courier.move(0, 1, game_world, jobs_manager)
                elif keys_pressed[pygame.K_LEFT]:
                    courier.move(-1, 0, game_world, jobs_manager) 
                elif keys_pressed[pygame.K_RIGHT]:
                    courier.move(1, 0, game_world, jobs_manager)


        # Ejecutar movimiento si hay dirección y no está en cooldown
        if (dx != 0 or dy != 0) and move_cooldown <= 0:
            save_game_state()  # Guardar estado para poder deshacer
            
            # Aplicar modificadores por clima y superficie
            stamina_cost_modifier = weather_manager.get_stamina_cost_multiplier()
            climate_mult = weather_manager.get_speed_multiplier()
            new_x, new_y = courier.x + dx, courier.y + dy

            # Verificar si la nueva posición es transitable
            if game_world.is_walkable(new_x, new_y):
                surface_weight = game_world.surface_weight_at(new_x, new_y)
                courier.move(
                    dx,
                    dy,
                    stamina_cost_modifier=stamina_cost_modifier,
                    surface_weight=surface_weight,
                    climate_mult=climate_mult,
                )
                move_cooldown = MOVE_COOLDOWN_TIME

        # Actualizar cooldown del movimiento
        if move_cooldown > 0:
            move_cooldown -= delta_time


        # ACTUALIZACIÓN DEL ESTADO DEL JUEGO
        courier_pos = (courier.x, courier.y)
        jobs_manager.update(elapsed_time, courier_pos)
        weather_manager.update(delta_time)

        if ai_courier:
            # Esto llama a update(), que internamente usa la estrategia para decidir y moverse.
            ai_courier.update(delta_time, game_world, weather_manager, jobs_manager)

        # Log periódico del estado del juego
        if int(elapsed_time) % 30 == 0 and int(elapsed_time) > 0:
            print(f"⏰ Tiempo: {int(elapsed_time)}s | Pedidos disponibles: {len(jobs_manager.available_jobs)}")

        # RENDERIZADO DEL JUEGO
        
        # Limpiar pantalla
        screen.fill((0, 0, 0))
        
        # Dibujar mundo, marcadores de pedidos y repartidor
        game_world.draw(screen)
        jobs_manager.draw_job_markers(screen, TILE_SIZE, courier_pos)
        
        # --- INICIO MODIFICACIÓN IA: Dibujar la IA ---
        ai_courier.draw(screen, TILE_SIZE) # Dibujar el repartidor IA primero
        hud.draw_ai_stats(screen, ai_courier)
        # --- FIN MODIFICACIÓN IA ---
        
        courier.draw(screen, TILE_SIZE) # Dibujar el repartidor jugador (para que quede encima si hay solapamiento)

        # Actualizar y dibujar efectos climáticos
        current_condition = weather_manager.get_current_condition()
        current_intensity = weather_manager.get_current_intensity()
        weather_visuals.update(delta_time, current_condition, current_intensity)
        weather_visuals.draw(screen)

        # Verificar proximidad a puntos de recogida/entrega
        near_pickup = False
        near_dropoff = False
        if not courier.inventory.is_empty():
            job = courier.inventory.current_job
            if job:
                if abs(courier.x - job.pickup_pos[0]) + abs(courier.y - job.pickup_pos[1]) == 1:
                    near_pickup = True
                if abs(courier.x - job.dropoff_pos[0]) + abs(courier.y - job.dropoff_pos[1]) == 1:
                    near_dropoff = True

        # Obtener peso de la superficie actual para el HUD
        current_surface_weight = game_world.surface_weight_at(courier.x, courier.y)
        current_speed_mult = weather_manager.get_speed_multiplier()

        # Dibujar HUD con información del juego
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
            current_surface_weight=current_surface_weight
        )

        # Actualizar y dibujar notificaciones
        notifier.update(delta_time)
        notifier.draw(screen, hud_area)

        # Actualizar pantalla
        pygame.display.flip()

    # Limpieza y salida
    pygame.quit()
    sys.exit()


# ------------------ FUNCIÓN PRINCIPAL CON MENÚ ------------------
def main():
    """
    Función principal que inicializa el juego y maneja el menú principal.
    """
    # Inicialización de Pygame
    pygame.init()

    # Tamaño de pantalla inicial para el menú
    INITIAL_SCREEN_WIDTH = 800
    INITIAL_SCREEN_HEIGHT = 600
    
    # Crear ventana inicial para el menú
    screen = pygame.display.set_mode((INITIAL_SCREEN_WIDTH, INITIAL_SCREEN_HEIGHT))
    pygame.display.set_caption("Courier Quest")
    
    # Crear menú principal
    menu = MainMenu(INITIAL_SCREEN_WIDTH, INITIAL_SCREEN_HEIGHT)
    
    # Bucle del menú
    clock = pygame.time.Clock()
    menu_running = True
    game_action = None
    
    while menu_running:
        # Manejo de eventos del menú
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu_running = False
                game_action = "quit"
            
            # Manejar eventos del menú (clic, teclas)
            action = menu.handle_event(event)
            if action:
                game_action = action
                menu_running = False
        
        # Dibujar menú
        menu.draw(screen)
        pygame.display.flip()
        clock.tick(60)
    
    # Salir del juego si se seleccionó "quit"
    if game_action == "quit":
        pygame.quit()
        sys.exit()
    
    ai_difficulty = AIDifficulty.MEDIUM # Valor por defecto

    # Iniciar el juego según la acción seleccionada
    if isinstance(game_action, dict):
        action_type = game_action.get("action")
        # Si el menú pasó una dificultad, la guardamos
        ai_difficulty = game_action.get("difficulty", AIDifficulty.MEDIUM)
    else:
        # Si es un string (ej. "new_game"), usamos el tipo directamente
        action_type = game_action
    
    # Iniciar el juego, pasando la dificultad de la IA
    start_game(action_type, ai_difficulty)


if __name__ == "__main__":
    main()
