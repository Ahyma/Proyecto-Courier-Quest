import pygame
import sys
import os

from api.client import APIClient
from api.cache import APICache
from game.courier import Courier
from game.world import World
# MODIFICADO: Solo importamos TILE_SIZE y PANEL_WIDTH
from game.constants import TILE_SIZE, PANEL_WIDTH
from game.weather_manager import WeatherManager
from game.weather_visuals import WeatherVisuals
from game.save_game import save_slot, load_slot
from game.score_board import save_score, load_scores 
# AÑADIDO: Importamos la clase HUD
from game.hud import HUD 
# from game.palette import WHITE # Descomentar si usas un color específico de palette

# --- 1. Funciones de Carga de Imágenes (SIN CAMBIOS) ---

def load_building_images():
    """
    Carga y devuelve un diccionario de imágenes de edificios por su tamaño.
    """
    building_images = {}
    image_names = {
        (3, 8): "edificio3x8.png",
        (4, 6): "edificio4x6.png",
        (4, 5): "edificio4x5.png",
        (5, 7): "edificio5x7.png",
        (6, 8): "edificio6x8.png",
        (7, 9): "edificio7x9.png"
    }
    
    base_path = "images"
    for size, filename in image_names.items():
        try:
            # Cargamos la imagen
            image = pygame.image.load(os.path.join(base_path, filename)).convert_alpha()
            building_images[size] = image
            print(f"Imagen de edificio {filename} ({size}) cargada con éxito.")
        except pygame.error as e:
            print(f"Error al cargar imagen de edificio {filename}: {e}. Se usará color de fallback.")
            building_images[size] = None # En caso de error, guardar None
            
    return building_images

def load_street_images():
    """
    Carga la imagen única del patrón de calle (calle.png).
    """
    base_path = "images"
    street_images = {}
    
    filename = "calle.png"
    
    try:
        # Cargamos y escalamos la imagen única a TILE_SIZE x TILE_SIZE
        image = pygame.image.load(os.path.join(base_path, filename)).convert_alpha()
        street_images["patron_base"] = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
        print(f"Imagen {filename} cargada con éxito.")
        
    except pygame.error as e:
        print(f"Error CRÍTICO al cargar imagen de calle {filename}: {e}. Se usará color de fallback.")
        street_images["patron_base"] = None 
            
    return street_images


# --- 2. Función Principal ---

def main():
    # Inicialización de Pygame
    pygame.init()

    # Inicialización de API y Cache
    api_cache = APICache()
    api_client = APIClient(api_cache)

    # Carga de datos
    map_data = api_client.get_map_data()
    weather_data = api_client.get_weather_data()
    
    if not map_data:
        print("Error CRÍTICO: No se pudo cargar los datos del mapa. Saliendo.")
        pygame.quit()
        sys.exit()

    # --- CÁLCULO DINÁMICO DEL TAMAÑO DE PANTALLA (NUEVO Y CRÍTICO) ---
    map_info = map_data.get('data', {})
    map_tile_width = map_info.get('width', 20)  # Tiles de ancho del mapa (fallback 20)
    map_tile_height = map_info.get('height', 15) # Tiles de alto del mapa (fallback 15)

    SCREEN_WIDTH = map_tile_width * TILE_SIZE
    SCREEN_HEIGHT = map_tile_height * TILE_SIZE

    # Configuración de la pantalla
    # AJUSTE: El ancho total es la suma del mapa más el panel HUD
    screen_size = (SCREEN_WIDTH + PANEL_WIDTH, SCREEN_HEIGHT) 
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("Courier Quest")

    # Inicialización del reloj para control de FPS
    clock = pygame.time.Clock()
    FPS = 60
    
    # Carga de imágenes (SIN CAMBIOS EN LA LÓGICA DE CARGA)
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
    # Asume que el punto de inicio es (0, 0) o lo obtienes del mapa.
    courier = Courier(start_x=0, start_y=0, image=repartidor_image)
    
    # Inicializar el clima y sus visuales
    weather_manager = WeatherManager(weather_data)
    # AJUSTE: weather_visuals debe recibir el tamaño de la pantalla de juego (sin el HUD)
    weather_visuals = WeatherVisuals((SCREEN_WIDTH, SCREEN_HEIGHT), TILE_SIZE)

    # --- INICIALIZACIÓN DEL HUD (NUEVO) ---
    # Define el área del HUD que comienza después del mapa de juego (SCREEN_WIDTH)
    hud_area = pygame.Rect(SCREEN_WIDTH, 0, PANEL_WIDTH, SCREEN_HEIGHT)
    hud = HUD(hud_area, SCREEN_HEIGHT, TILE_SIZE)
    # -------------------------------------
    
    # --- variables de control de tiempo y meta ---
    elapsed_time = 0.0
    max_time = map_info.get("max_time", 900)  # segundos
    goal_income = map_info.get("goal", 0)

    running = True
    while running:
        delta_time = clock.tick(FPS) / 1000.0 # Tiempo en segundos
        elapsed_time += delta_time
        remaining_time = max_time - elapsed_time

        # Condición de derrota por tiempo
        if remaining_time <= 0:
            print("Game Over: se acabó el tiempo.")
            running = False

        # Condición de victoria por meta alcanzada
        if getattr(courier, "income", 0) >= goal_income:
            print("¡Victoria! Meta alcanzada.")
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                dx, dy = 0, 0
                if event.key == pygame.K_UP: dy = -1
                elif event.key == pygame.K_DOWN: dy = 1
                elif event.key == pygame.K_LEFT: dx = -1
                elif event.key == pygame.K_RIGHT: dx = 1
                elif event.key == pygame.K_s:
                    data_to_save = courier.get_save_state()
                    save_slot(1, data_to_save)
                    print("Partida guardada.")
                    continue
                elif event.key == pygame.K_l:
                    try:
                        loaded_data = load_slot(1)
                        if loaded_data:
                            courier.load_state(loaded_data)
                            print("Partida cargada.")
                        else:
                            print("Archivo de guardado vacío o corrupto.")
                    except FileNotFoundError:
                        print("No se encontró 'slot1.sav'.")
                    continue

                # --- integración con surface_weight y clima ---
                stamina_cost_modifier = weather_manager.get_stamina_cost_multiplier()
                climate_mult = weather_manager.get_speed_multiplier()
                new_x, new_y = courier.x + dx, courier.y + dy
                if game_world.is_walkable(new_x, new_y):
                    surface_weight = game_world.surface_weight_at(new_x, new_y)
                    courier.move(dx, dy,
                                 stamina_cost_modifier=stamina_cost_modifier,
                                 surface_weight=surface_weight,
                                 climate_mult=climate_mult)
                #se pasa toda la info para calcular la formula oficial de velocidad

        weather_manager.update(delta_time)

        screen.fill((0, 0, 0))
        game_world.draw(screen)
        courier.draw(screen, TILE_SIZE)

        current_condition = weather_manager.get_current_condition()
        weather_visuals.update(delta_time, current_condition, weather_manager.get_current_intensity()) #pasa intensidad actual del manager
        weather_visuals.draw(screen)

        current_speed_mult = weather_manager.get_speed_multiplier()
        hud.draw(screen, courier, current_condition, current_speed_mult)

        pygame.display.flip()


    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()