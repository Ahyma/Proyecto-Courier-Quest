import pygame
import sys
import os

from api.client import APIClient
from api.cache import APICache
from game.courier import Courier
from game.world import World
from game.constants import TILE_SIZE

def main():
    """
    Función principal que ejecuta el bucle de juego.
    """
    # Inicializar cliente de API y caché
    api_cache = APICache()
    api_client = APIClient(api_cache=api_cache)

    # Obtener datos del mapa desde el API o la caché
    map_data = api_client.get_map_data()
    if not map_data or 'data' not in map_data:
        print("No se pudo cargar el mapa. Saliendo del juego.")
        sys.exit()

    map_info = map_data.get('data', {})
    map_width = map_info.get('width', 0)
    map_height = map_info.get('height', 0)
    
    if map_width == 0 or map_height == 0:
        print("Las dimensiones del mapa no son válidas. Saliendo del juego.")
        sys.exit()

    # Redefinir las dimensiones de la pantalla en función del mapa
    screen_width = map_width * TILE_SIZE
    screen_height = map_height * TILE_SIZE

    # Inicializar Pygame con las dimensiones correctas
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Courier Quest")

    # Cargar la imagen del repartidor
    try:
        repartidor_image = pygame.image.load(os.path.join("images", "repartidor.png")).convert_alpha()
        repartidor_image = pygame.transform.scale(repartidor_image, (TILE_SIZE, TILE_SIZE))
    except pygame.error as e:
        print(f"Error al cargar la imagen del repartidor: {e}")
        repartidor_image = None

    # Cargar la imagen del edificio
    try:
        # 1. Carga la imagen del edificio
        edificio_image = pygame.image.load(os.path.join("images", "edificio.png")).convert()
        
        # 2. Establece el color negro (0, 0, 0) como el color transparente
        #    Esto es crucial para eliminar el fondo sólido
        edificio_image.set_colorkey((0, 0, 0))

        # 3. Escala la imagen al tamaño del tile
        edificio_image = pygame.transform.scale(edificio_image, (TILE_SIZE, TILE_SIZE))
    except pygame.error as e:
        print(f"Error al cargar la imagen del edificio: {e}")
        edificio_image = None

    # Inicializar el mundo del juego y el repartidor
    game_world = World(map_data=map_data, building_image=edificio_image)
    courier = Courier(start_x=0, start_y=0, image=repartidor_image)

    running = True
    while running:
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
                
                # Mover el repartidor si el movimiento es válido
                if game_world.is_walkable(courier.x + dx, courier.y + dy):
                    courier.move(dx, dy)
        
        # Lógica de renderizado
        screen.fill((0, 0, 0)) # Color de fondo
        game_world.draw(screen)
        courier.draw(screen, TILE_SIZE)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()