import pygame
import sys

from api.client import APIClient
from api.cache import APICache
from game.courier import Courier
from game.world import World
from game.constants import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
from game.palette import BLACK

def main():
    """
    Función principal que ejecuta el bucle de juego.
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Courier Quest")

    # Inicializar cliente de API y caché
    api_cache = APICache()
    api_client = APIClient(api_cache=api_cache)

    # Obtener datos del mapa desde el API o la caché
    map_data = api_client.get_map_data()
    if not map_data:
        print("No se pudo cargar el mapa. Saliendo del juego.")
        pygame.quit()
        sys.exit()

    # Inicializar el mundo del juego
    game_world = World(map_data=map_data)
    
    # Crear la instancia del repartidor
    courier = Courier(start_x=0, start_y=0, image=None) # Ajusta el cargado de la imagen

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
        screen.fill(BLACK)
        game_world.draw(screen)
        courier.draw(screen, TILE_SIZE)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()