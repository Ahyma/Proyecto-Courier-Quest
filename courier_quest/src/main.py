import pygame
import sys
import os

from api.client import APIClient
from api.cache import APICache
from game.courier import Courier
from game.world import World
from game.constants import TILE_SIZE
from game.weather_manager import WeatherManager
from game.weather_visuals import WeatherVisuals

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
    
    for size, filename in image_names.items():
        try:
            image_path = os.path.join("images", filename)
            image = pygame.image.load(image_path).convert_alpha()
            building_images[size] = image
        except pygame.error as e:
            print(f"Error al cargar la imagen {filename}: {e}")
            building_images[size] = None

    return building_images

def load_street_images(tile_size):
    """
    Carga y devuelve un diccionario de imágenes de calles para autotiling.
    """
    street_images = {}
    image_names = {
        "centro": "calle_centro.png",
        "horizontal": "calle_horizontal.png",
        "vertical": "calle_vertical.png",
        "borde_arriba": "calle_borde_arriba.png",
        "borde_abajo": "calle_borde_abajo.png",
        "borde_izquierda": "calle_borde_izquierda.png",
        "borde_derecha": "calle_borde_derecha.png",
        "esquina_arriba_izquierda": "calle_esquina_arriba_izquierda.png",
        "esquina_arriba_derecha": "calle_esquina_arriba_derecha.png",
        "esquina_abajo_izquierda": "calle_esquina_abajo_izquierda.png",
        "esquina_abajo_derecha": "calle_esquina_abajo_derecha.png",
    }
    
    for key, filename in image_names.items():
        try:
            image_path = os.path.join("images", filename)
            image = pygame.image.load(image_path).convert_alpha()
            street_images[key] = pygame.transform.scale(image, (tile_size, tile_size))
        except pygame.error as e:
            print(f"Error al cargar la imagen de calle {filename}: {e}")
            street_images[key] = None
    
    return street_images

def main():
    
    #Función principal que ejecuta el bucle de juego
    api_cache = APICache()
    api_client = APIClient(api_cache=api_cache)

    map_data = api_client.get_map_data()
    if not map_data or 'data' not in map_data:
        print("No se pudo cargar el mapa. Saliendo del juego.")
        sys.exit()

     # Carga los datos del clima e inicializa el manejador
    weather_data = api_client.get_weather_data()
    if not weather_data:
        print("No se pudieron cargar los datos del clima. Saliendo del juego.")
        sys.exit()
    weather_manager = WeatherManager(weather_data)

    map_info = map_data.get('data', {})
    map_width = map_info.get('width', 0)
    map_height = map_info.get('height', 0)
    
    if map_width == 0 or map_height == 0:
        print("Las dimensiones del mapa no son válidas. Saliendo del juego.")
        sys.exit()

    screen_width = map_width * TILE_SIZE
    screen_height = map_height * TILE_SIZE

    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Courier Quest")

    clock = pygame.time.Clock()
    #weather_visuals = WeatherVisuals(screen.get_size())
    weather_visuals = WeatherVisuals(screen.get_size(), TILE_SIZE)

    # ---- Cargar la imagen del repartidor ----
    try:
        repartidor_image = pygame.image.load(os.path.join("images", "repartidor.png")).convert_alpha()
        repartidor_image = pygame.transform.scale(repartidor_image, (TILE_SIZE, TILE_SIZE))
    except pygame.error as e:
        print(f"Error al cargar la imagen del repartidor: {e}")
        repartidor_image = None
    
    # ---- Cargar la imagen de los edificios ----
    building_images = load_building_images()
    if not building_images:
        print("No se pudieron cargar las imágenes de edificios. Saliendo del juego.")
        sys.exit()

    # ---- Cargar las imágenes de calles ----
    street_images = load_street_images(TILE_SIZE)
    if not street_images:
        print("No se pudieron cargar las imágenes de calles. Saliendo del juego.")
        sys.exit()

    # ---- Cargar la imagen del césped ----
    try:
        cesped_image = pygame.image.load(os.path.join("images", "cesped.png")).convert_alpha()
        cesped_image = pygame.transform.scale(cesped_image, (TILE_SIZE, TILE_SIZE))
    except pygame.error as e:
        print(f"Error al cargar la imagen del césped: {e}")
        cesped_image = None

    # Inicializar el mundo del juego y el repartidor
    game_world = World(
        map_data=map_data, 
        building_images=building_images, 
        grass_image=cesped_image, 
        street_images=street_images
    )
    courier = Courier(start_x=0, start_y=0, image=repartidor_image)

    running = True
    while running:
        # Tiempo en segundos desde el último frame
        delta_time = clock.tick(60) / 1000.0

        # Actualiza el clima
        weather_manager.update(delta_time)

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
                
                # Obtiene el costo extra de resistencia del clima
                stamina_cost_modifier = weather_manager.get_stamina_cost_multiplier()
                
                if game_world.is_walkable(courier.x + dx, courier.y + dy):
                    # Pasa el costo de resistencia extra al método move
                    courier.move(dx, dy, stamina_cost_modifier)
        
        # --- Lógica de dibujado ---
        screen.fill((0, 0, 0))
        game_world.draw(screen)
        courier.draw(screen, TILE_SIZE)

        # Lógica para dibujar el clima
        # 1. Actualiza el estado de las animaciones
        current_condition = weather_manager.get_current_condition()
        weather_visuals.update(delta_time, current_condition)

        # 2. Dibuja los efectos del clima
        weather_visuals.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()