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

def load_building_images():
    """
    Carga y devuelve un diccionario de imágenes de edificios por su tamaño.
    """
    building_images = {}
    image_names = {
        (3, 8): "edificio3x8.png",
        (5, 5): "edificio4x6.png",
        (6, 5): "edificio4x5.png",
        (7, 6): "edificio5x7.png",
        (7, 8): "edificio6x8.png",
        (8, 9): "edificio7x9.png"
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
    """
    Carga la imagen única del patrón de calle (calle.png).
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

def draw_current_job_info(screen, current_job, elapsed_time, panel_width, screen_width):
    """Dibuja información del pedido actual en inventario"""
    if not current_job:
        return
        
    font = pygame.font.Font(None, 22)
    
    # Información básica
    title = font.render("PEDIDO ACTUAL:", True, (255, 255, 0))
    screen.blit(title, (screen_width + 20, 400))
    
    id_text = font.render(f"ID: {current_job.id}", True, (255, 255, 255))
    screen.blit(id_text, (screen_width + 30, 430))
    
    payout_text = font.render(f"Pago: ${current_job.payout}", True, (255, 255, 255))
    screen.blit(payout_text, (screen_width + 30, 460))

def main():
    # Inicialización de Pygame
    pygame.init()

    # Inicialización de API y Cache
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

    # --- DEFINIR map_info AQUÍ ---
    map_info = map_data.get('data', {})

    # Ahora sí podemos usar map_info
    game_start_time = datetime.fromisoformat(map_info.get("start_time", "2025-09-01T12:00:00Z"))
    jobs_manager = JobsManager(jobs_data, game_start_time)

    # --- CÁLCULO DINÁMICO DEL TAMAÑO DE PANTALLA ---
    map_tile_width = map_info.get('width', 20)
    map_tile_height = map_info.get('height', 15)

    SCREEN_WIDTH = map_tile_width * TILE_SIZE
    SCREEN_HEIGHT = map_tile_height * TILE_SIZE

    # Configuración de la pantalla
    screen_size = (SCREEN_WIDTH + PANEL_WIDTH, SCREEN_HEIGHT) 
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("Courier Quest")
    
    # Inicialización del reloj para control de FPS
    clock = pygame.time.Clock()
    FPS = 60
    
    # Carga de imágenes
    building_images = load_building_images()
    street_images = load_street_images()
    
    # Cargar imagen de césped
    try:
        cesped_image = pygame.image.load(os.path.join("images", "cesped.png")).convert_alpha()
        cesped_image = pygame.transform.scale(cesped_image, (TILE_SIZE, TILE_SIZE))
    except pygame.error as e:
        print(f"Error al cargar la imagen del césped: {e}")
        cesped_image = None

    # Cargar imagen del repartidor
    try:
        repartidor_image = pygame.image.load(os.path.join("images", "repartidor.png")).convert_alpha()
        repartidor_image = pygame.transform.scale(repartidor_image, (TILE_SIZE, TILE_SIZE))
    except pygame.error as e:
        print(f"Error al cargar la imagen del repartidor: {e}")
        repartidor_image = None
        
    # Inicializar el mundo del juego y el repartidor
    game_world = World(
        map_data=map_data, 
        building_images=building_images, 
        grass_image=cesped_image, 
        street_images=street_images
    )
    
    # Inicializar courier
    courier = Courier(start_x=0, start_y=0, image=repartidor_image)
    
    # Inicializar el clima
    weather_manager = WeatherManager(weather_data)
    weather_visuals = WeatherVisuals((SCREEN_WIDTH, SCREEN_HEIGHT), TILE_SIZE)

    # Inicializar HUD
    hud_area = pygame.Rect(SCREEN_WIDTH, 0, PANEL_WIDTH, SCREEN_HEIGHT)
    hud = HUD(hud_area, SCREEN_HEIGHT, TILE_SIZE)
    
    # --- GENERAR PEDIDOS SI NO HAY DATOS ---
    if not jobs_data or not jobs_data.get('data'):
        print("📦 Generando pedidos aleatorios...")
        jobs_manager.generate_random_jobs(game_world, num_jobs=15)
        
        # --- VERIFICACIÓN DE PEDIDOS GENERADOS ---
        print("🔍 VERIFICANDO PEDIDOS GENERADOS:")
        print(f"   Total de pedidos: {len(jobs_manager.all_jobs)}")
        print(f"   Pedidos disponibles: {len(jobs_manager.available_jobs)}")

        for i, job in enumerate(jobs_manager.all_jobs):
            print(f"   {i+1}. {job.id} - Pos: {job.pickup_pos} - Release: {job.release_time}s - Estado: {job.state}")
    else:
        print("📦 Usando pedidos del JSON")
        # También verificar los pedidos del JSON
        print("🔍 VERIFICANDO PEDIDOS DEL JSON:")
        print(f"   Total de pedidos: {len(jobs_manager.all_jobs)}")
        print(f"   Pedidos disponibles: {len(jobs_manager.available_jobs)}")
    
    # variables de control de tiempo y meta
    elapsed_time = 0.0
    max_time = map_info.get("max_time", 900)  # segundos
    goal_income = map_info.get("goal", 0)

    # Variables para control de interfaz
    show_available_jobs = False
    selected_job_index = 0
    
    # --- BUCLE PRINCIPAL DEL JUEGO ---
    running = True
    while running:
        delta_time = clock.tick(FPS) / 1000.0 # Tiempo en segundos
        elapsed_time += delta_time
        remaining_time = max_time - elapsed_time

        # --- CONDICIONES DE VICTORIA/DERROTA ---
        # Derrota por tiempo
        if remaining_time <= 0:
            print("Game Over: se acabó el tiempo.")
            running = False

        # Derrota por reputación baja
        if courier.reputation < 20:
            print("Game Over: reputación muy baja.")
            running = False

        # Victoria por meta alcanzada
        if courier.income >= goal_income:
            print("¡Victoria! Meta alcanzada.")
            # Calcular puntaje final y guardar
            final_score = courier.income
            if courier.reputation >= 90:
                final_score *= 1.05  # Bono por reputación alta
            save_score({"score": final_score, "income": courier.income, "time": elapsed_time})
            running = False

        # --- ACTUALIZACIONES DEL ESTADO DEL JUEGO ---
        courier_pos = (courier.x, courier.y)
        jobs_manager.update(elapsed_time, courier_pos)
        weather_manager.update(delta_time)

        # --- DEBUG: Mostrar estado de pedidos periódicamente ---
        if int(elapsed_time) % 30 == 0 and int(elapsed_time) > 0:  # Cada 30 segundos
            available_count = len(jobs_manager.available_jobs)
            print(f"⏰ Tiempo: {int(elapsed_time)}s | Pedidos disponibles: {available_count}")

        # --- MANEJO DE EVENTOS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                # --- MOVIMIENTO DEL COURIER ---
                dx, dy = 0, 0
                if event.key == pygame.K_UP: dy = -1
                elif event.key == pygame.K_DOWN: dy = 1
                elif event.key == pygame.K_LEFT: dx = -1
                elif event.key == pygame.K_RIGHT: dx = 1
                
                # --- SISTEMA DE PEDIDOS ---
                elif event.key == pygame.K_SPACE:  # ESPACIO - Recoger pedido
                    try:
                        nearby_jobs = jobs_manager.get_available_jobs_nearby(courier_pos, max_distance=1)
                        pickup_success = False
                        
                        for job in nearby_jobs:
                            if job.is_at_pickup(courier_pos):
                                if jobs_manager.try_pickup_job(job.id, courier_pos, courier.inventory, elapsed_time):
                                    print(f"✅ Pedido {job.id} recogido! +${job.payout}")
                                    pickup_success = True
                                    break
                        
                        if not pickup_success:
                            print("❌ No hay pedidos para recoger desde esta posición")
                            
                    except Exception as e:
                        print(f"Error en recogida: {e}")
                
                elif event.key == pygame.K_e:  # TECLA E - Entregar pedido
                    if not courier.inventory.is_empty():
                        delivered_job = jobs_manager.try_deliver_job(courier.inventory, courier_pos, elapsed_time)
                        if delivered_job:
                            # Calcular pago con bono de reputación
                            base_payout = delivered_job.payout
                            if courier.reputation >= 90:
                                base_payout *= 1.05
                                print("💰 ¡Bono de reputación aplicado! +5%")
                            
                            courier.income += base_payout
                            reputation_change = delivered_job.calculate_reputation_change()
                            courier.reputation = max(0, min(100, courier.reputation + reputation_change))
                            
                            print(f"🎉 Pedido {delivered_job.id} entregado! +${base_payout}")
                        else:
                            print("❌ No estás en posición de entrega")
                    else:
                        print("❌ No tienes pedidos para entregar")
                
                elif event.key == pygame.K_TAB:  # Tab - Navegar inventario
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        courier.inventory.previous_job()
                        print("Pedido anterior seleccionado")
                    else:
                        courier.inventory.next_job()
                        print("Siguiente pedido seleccionado")
                
                elif event.key == pygame.K_c:  # Tecla C - Cancelar pedido actual
                    current_job = courier.inventory.current_job
                    if current_job and current_job.cancel():
                        cancelled_job = courier.inventory.remove_current_job()
                        courier.reputation = max(0, courier.reputation - 4)
                        print(f"Pedido {cancelled_job.id} cancelado. Reputación -4")
                
                # --- CONTROLES DE ORDENAMIENTO ---
                elif event.key == pygame.K_F1:  # F1 - Ordenar por prioridad
                    if not courier.inventory.is_empty():
                        sorted_jobs = courier.inventory.get_jobs_sorted_by_priority()
                        print("📊 Pedidos ordenados por PRIORIDAD:")
                        for i, job in enumerate(sorted_jobs):
                            print(f"   {i+1}. {job.id} - Prioridad: {job.priority} - ${job.payout}")
                
                elif event.key == pygame.K_F2:  # F2 - Ordenar por deadline
                    if not courier.inventory.is_empty():
                        sorted_jobs = courier.inventory.get_jobs_sorted_by_deadline(elapsed_time)
                        print("⏰ Pedidos ordenados por DEADLINE:")
                        for i, job in enumerate(sorted_jobs):
                            time_left = job.get_time_until_deadline(elapsed_time)
                            if time_left != float('inf'):
                                mins = int(time_left // 60)
                                secs = int(time_left % 60)
                                print(f"   {i+1}. {job.id} - Tiempo: {mins:02d}:{secs:02d}")
                            else:
                                print(f"   {i+1}. {job.id} - Sin deadline")
                
                elif event.key == pygame.K_F3:  # F3 - Ordenar por pago
                    if not courier.inventory.is_empty():
                        sorted_jobs = courier.inventory.get_jobs_sorted_by_payout()
                        print("💰 Pedidos ordenados por PAGO:")
                        for i, job in enumerate(sorted_jobs):
                            print(f"   {i+1}. {job.id} - ${job.payout} - Prioridad: {job.priority}")
                
                elif event.key == pygame.K_F4:  # F4 - Volver al orden original
                    print("🔄 Orden original del inventario")
                
                # --- SISTEMA DE GUARDADO/CARGA ---
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    data_to_save = {
                        "courier": courier.get_save_state(),
                        "elapsed_time": elapsed_time
                    }
                    save_slot("slot1.sav", data_to_save)
                    print("Partida guardada.")
                
                elif event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    try:
                        loaded_data = load_slot("slot1.sav")
                        if loaded_data:
                            courier.load_state(loaded_data.get("courier", {}))
                            elapsed_time = loaded_data.get("elapsed_time", 0.0)
                            print("Partida cargada.")
                        else:
                            print("Archivo de guardado vacío o corrupto.")
                    except FileNotFoundError:
                        print("No se encontró 'slot1.sav'.")
                
                # --- MOVIMIENTO ---
                if dx != 0 or dy != 0:
                    stamina_cost_modifier = weather_manager.get_stamina_cost_multiplier()
                    climate_mult = weather_manager.get_speed_multiplier()
                    new_x, new_y = courier.x + dx, courier.y + dy
                    
                    if game_world.is_walkable(new_x, new_y):
                        surface_weight = game_world.surface_weight_at(new_x, new_y)
                        courier.move(dx, dy,
                                    stamina_cost_modifier=stamina_cost_modifier,
                                    surface_weight=surface_weight,
                                    climate_mult=climate_mult)

        # --- RENDERIZADO ---
        screen.fill((0, 0, 0))
        
        # Dibujar mundo
        game_world.draw(screen)
        
        # Dibujar marcadores de pedidos
        jobs_manager.draw_job_markers(screen, TILE_SIZE, courier_pos)
        
        # Dibujar courier
        courier.draw(screen, TILE_SIZE)
        
        # Dibujar efectos climáticos
        current_condition = weather_manager.get_current_condition()
        current_intensity = weather_manager.get_current_intensity()
        weather_visuals.update(delta_time, current_condition, current_intensity)
        weather_visuals.draw(screen)
        
        # Dibujar HUD
        current_speed_mult = weather_manager.get_speed_multiplier()
        hud.draw(screen, courier, current_condition, current_speed_mult, remaining_time, goal_income)
        
        # Dibujar información del pedido actual
        if not courier.inventory.is_empty():
            draw_current_job_info(screen, courier.inventory.current_job, elapsed_time, PANEL_WIDTH, SCREEN_WIDTH)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
