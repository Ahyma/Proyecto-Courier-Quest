import pygame
import sys
import os

from api.client import APIClient
from api.cache import APICache
from game.courier import Courier
from game.world import World
# Solo importamos TILE_SIZE. SCREEN_WIDTH y SCREEN_HEIGHT se calculan en main().
from game.constants import TILE_SIZE 
from game.weather_manager import WeatherManager
from game.weather_visuals import WeatherVisuals
from game.save_game import save_slot, load_slot
from game.score_board import save_score, load_scores 

# --- 1. Funciones de Carga de Imágenes ---

def load_building_images():
    """
    Carga y devuelve un diccionario de imágenes de edificios por su tamaño.
    """
    building_images = {}
    image_names = {
        (2, 2): "edificio2x2.png",
        (3, 3): "edificio3x3.png",
        (3, 4): "edificio3x4.png",
        (3, 8): "edificio5x5.png", 
        (4, 4): "edificio4x4.png",
        (5, 4): "edificio5x4.png",
        (4, 5): "edificio2x2.png",
        (4, 6): "edificio5x4.png",
        (5, 5): "edificio4x4.png",
        (6, 5): "edificio6x5.png",
        (6, 8): "edificio6x8.png",
        (7, 7): "edificio7x7.png",
        (7, 9): "edificio5x7.png",
        (5, 7): "edificio7x9.png"
    }
    
    base_path = "images"
    for size, filename in image_names.items():
        try:
            image = pygame.image.load(os.path.join(base_path, filename)).convert_alpha()
            building_images[size] = image
        except pygame.error as e:
            print(f"Error al cargar imagen de edificio {filename} para tamaño {size}: {e}")
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
    pygame.init()
    
    # Inicialización de API y Caché
    api_cache = APICache()
    api_client = APIClient(api_cache)

    # Cargar datos del mundo (usa API o cache/local)
    map_data = api_client.get_map_data()
    weather_data = api_client.get_weather_data()
    
    if not map_data or not weather_data:
        print("Error: No se pudieron cargar los datos esenciales del mapa o clima.")
        pygame.quit()
        sys.exit()

    # --- LÓGICA DE CÁLCULO DE PANTALLA DINÁMICA ---
    # Extraer las dimensiones del mapa
    map_width = map_data.get('data', {}).get('width', 0)
    map_height = map_data.get('data', {}).get('height', 0)

    # Validar dimensiones
    if map_width <= 0 or map_height <= 0:
        print(f"Error: Las dimensiones del mapa no son válidas (W:{map_width}, H:{map_height}).")
        pygame.quit()
        sys.exit()

    # Calcular las dimensiones de la pantalla
    SCREEN_WIDTH = map_width * TILE_SIZE
    SCREEN_HEIGHT = map_height * TILE_SIZE
    # -----------------------------------------------
    
    # Configuración de la pantalla
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Courier Quest")

    # Inicialización del reloj y delta time
    clock = pygame.time.Clock()
    
    # --- Carga de Recursos Visuales ---
    building_images = load_building_images()
    street_images = load_street_images()
    
    # Carga de la imagen de césped
    cesped_image = None
    try:
        cesped_image = pygame.image.load(os.path.join("images", "cesped.png")).convert_alpha()
        cesped_image = pygame.transform.scale(cesped_image, (TILE_SIZE, TILE_SIZE))
    except pygame.error as e:
        print(f"Error al cargar la imagen del césped: {e}. Se usará color de fallback.")
        
    # Carga de la imagen del repartidor
    repartidor_image = None
    try:
        repartidor_image = pygame.image.load(os.path.join("images", "repartidor.png")).convert_alpha()
        repartidor_image = pygame.transform.scale(repartidor_image, (TILE_SIZE, TILE_SIZE))
    except pygame.error as e:
        print(f"Error al cargar la imagen del repartidor: {e}. Se usará dibujo simple.")


    # --- Inicialización de Lógica de Juego ---
    game_world = World(
        map_data=map_data, 
        building_images=building_images, 
        grass_image=cesped_image, 
        street_images=street_images
    )
    courier = Courier(start_x=0, start_y=0, image=repartidor_image)
    weather_manager = WeatherManager(weather_data)
    weather_visuals = WeatherVisuals(screen.get_size(), TILE_SIZE)

    running = True
    while running:
        # Calcular delta time (tiempo transcurrido desde el último frame)
        delta_time = clock.tick(60) / 1000.0 # Convertir milisegundos a segundos

        # --- Manejo de Eventos ---
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

                # Teclas de Guardado/Carga
                elif event.key == pygame.K_s:
                    save_slot("slot1.sav", courier)
                    continue
                elif event.key == pygame.K_l:
                    try:
                        loaded_data = load_slot("slot1.sav")
                        if loaded_data:
                            courier.load_state(loaded_data)
                            print("Partida cargada con éxito.")
                        else:
                            print("El archivo de guardado está vacío o corrupto.")
                    except FileNotFoundError:
                        print("No se encontró el archivo de guardado 'slot1.sav'.")
                    except Exception as e:
                        print(f"Error al cargar la partida: {e}")
                    continue 

                # Obtiene el costo extra de resistencia del clima
                stamina_cost_modifier = weather_manager.get_stamina_cost_multiplier()
                
                # Mover si es transitable
                if game_world.is_walkable(courier.x + dx, courier.y + dy):
                    # Pasa el costo de resistencia extra al método move
                    courier.move(dx, dy, stamina_cost_modifier)
        
        # --- Lógica de Actualización ---
        weather_manager.update(delta_time)
        
        # --- Lógica de dibujado ---
        screen.fill((0, 0, 0)) # Limpiar pantalla
        game_world.draw(screen)
        courier.draw(screen, TILE_SIZE)

        # Lógica para dibujar el clima
        current_condition = weather_manager.get_current_condition()
        weather_visuals.update(delta_time, current_condition)
        weather_visuals.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()