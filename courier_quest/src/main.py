import pygame
import sys
import os
from datetime import datetime

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
from game.reputation import ReputationSystem  # ⬅️ para deltas de reputación (cancel/expired)
from game.notifications import NotificationsOverlay  # ⬅️ NUEVO: overlay de notificaciones


# ------------------ CARGA DE IMÁGENES ------------------
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

    base_path = "images"
    for size, filename in image_names.items():
        try:
            image = pygame.image.load(os.path.join(base_path, filename)).convert_alpha()
            building_images[size] = image
            print(f"Imagen de edificio {filename} ({size}) cargada con éxito.")
        except pygame.error as e:
            print(f"Error al cargar imagen de edificio {filename}: {e}. Se usará color de fallback.")
            building_images[size] = None
    return building_images


def load_street_images():
    """Carga la imagen única del patrón de calle (calle.png)."""
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


# ------------------ JUEGO ------------------
def main():
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
    pygame.display.set_caption("Courier Quest")

    # Reloj
    clock = pygame.time.Clock()
    FPS = 60

    # Imágenes
    building_images = load_building_images()
    street_images = load_street_images()

    # Césped
    try:
        cesped_image = pygame.image.load(os.path.join("images", "cesped.png")).convert_alpha()
        cesped_image = pygame.transform.scale(cesped_image, (TILE_SIZE, TILE_SIZE))
    except pygame.error as e:
        print(f"Error al cargar la imagen del césped: {e}")
        cesped_image = None

    # Repartidor
    try:
        repartidor_image = pygame.image.load(os.path.join("images", "repartidor.png")).convert_alpha()
        repartidor_image = pygame.transform.scale(repartidor_image, (TILE_SIZE, TILE_SIZE))
    except pygame.error as e:
        print(f"Error al cargar la imagen del repartidor: {e}")
        repartidor_image = None

    # Mundo y sistemas
    game_world = World(
        map_data=map_data,
        building_images=building_images,
        grass_image=cesped_image,
        street_images=street_images,
    )
    courier = Courier(start_x=0, start_y=0, image=repartidor_image)

    weather_manager = WeatherManager(weather_data)
    weather_visuals = WeatherVisuals((SCREEN_WIDTH, SCREEN_HEIGHT), TILE_SIZE)

    # HUD
    hud_area = pygame.Rect(SCREEN_WIDTH, 0, PANEL_WIDTH, SCREEN_HEIGHT)
    hud = HUD(hud_area, SCREEN_HEIGHT, TILE_SIZE)

    # NUEVO: overlay de notificaciones (se dibuja dentro del panel/HUD)
    notifier = NotificationsOverlay(panel_width=PANEL_WIDTH, screen_height=SCREEN_HEIGHT)

    # Generar pedidos si no hay JSON utilizable
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

    # Bucle principal
    running = True
    while running:
        delta_time = clock.tick(FPS) / 1000.0
        elapsed_time += delta_time
        remaining_time = max_time - elapsed_time

        # Condiciones fin de juego
        if remaining_time <= 0:
            print("Game Over: se acabó el tiempo.")
            # ⬇️ Guardar score también en derrota por tiempo
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
            # ⬇️ Guardar score también en derrota por reputación
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
                final_score *= 1.05  # Bono por reputación alta (muestra final)
            save_score({
                "score": round(final_score, 2),
                "income": round(courier.income, 2),
                "time": round(elapsed_time, 2),
                "reputation": int(courier.reputation),
            })
            notifier.success("¡Meta alcanzada! Score guardado")
            running = False

        # Actualizaciones del estado
        courier_pos = (courier.x, courier.y)
        jobs_manager.update(elapsed_time, courier_pos)
        weather_manager.update(delta_time)

        # Debug periódico
        if int(elapsed_time) % 30 == 0 and int(elapsed_time) > 0:
            print(f"⏰ Tiempo: {int(elapsed_time)}s | Pedidos disponibles: {len(jobs_manager.available_jobs)}")

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

                # --- Pedidos ---
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
                        # Guardamos referencia por si expira justo antes de entregar
                        _before = courier.inventory.current_job
                        delivered_job = jobs_manager.try_deliver_job(courier.inventory, courier_pos, elapsed_time)

                        if delivered_job:
                            # Bono por reputación se toma del Courier (por si en el futuro cambia)
                            mult = courier.get_reputation_multiplier()
                            base_payout = delivered_job.payout * mult
                            if mult > 1.0:
                                print("💰 ¡Bono de reputación aplicado! +5%")
                                notifier.info("Bono +5% por reputación ≥90")

                            courier.income += base_payout

                            # Reputación según puntualidad (y racha interna del Courier)
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
                                # ⬇️ Guardar score también en derrota inmediata
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
                            # Si no se entregó y el job se marcó como expirado dentro de try_deliver_job,
                            # aplicamos penalización -6.
                            if _before and _before.state == "expired":
                                delta = ReputationSystem.for_delivery(
                                    # status "expired" para usar la tabla (-6)
                                    res=type("R", (), {"status": "expired"})()  # pequeño objeto con status
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

                # --- NUEVO: Ver pedidos cercanos ---
                elif event.key == pygame.K_a:
                    try:
                        nearby = jobs_manager.get_available_jobs_nearby(courier_pos, max_distance=3)
                        if not nearby:
                            print("🔎 No hay pedidos cercanos (≤3 celdas).")
                            notifier.info("No hay pedidos cercanos (≤3)")
                        else:
                            print(f"🔎 Pedidos cercanos ({len(nearby)}):")
                            for j in nearby:
                                # Tiempo restante si Job lo soporta
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

                # --- Ordenamiento real ---
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

                # --- Guardado/Carga ---
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
                        )

        # ---------- RENDER ----------
        screen.fill((0, 0, 0))
        game_world.draw(screen)
        jobs_manager.draw_job_markers(screen, TILE_SIZE, courier_pos)
        courier.draw(screen, TILE_SIZE)

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

        # HUD
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
            current_game_time=elapsed_time  # ⬅️ NUEVO: para tiempo restante del pedido en la card
        )

        # NUEVO: overlay de notificaciones (sobre el panel/HUD)
        notifier.update(delta_time)
        notifier.draw(screen, hud_area)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
