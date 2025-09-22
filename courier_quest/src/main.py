#es nuestro main
"""import pygame
import os
from api.api_handler import get_map_data, get_jobs_data, get_weather_data
from courier import Courier

# Obtener los datos del mapa al inicio del programa
map_data = get_map_data()
jobs_data = get_jobs_data()
weather_data = get_weather_data()

# Si los datos no se pudieron cargar, sal del programa
if not map_data:
    print("No se pudo cargar el mapa. Saliendo del juego.")
    pygame.quit()
    exit()

# CORRECCIÓN: Acceder a los datos dentro de 'data'
data = map_data.get('data', {})

# Ahora, puedes acceder a los datos del mapa
print("--- Detalles del Mapa ---")
print(f"Versión: {map_data.get('version')}")
print(f"Ancho: {data.get('width')}")
print(f"Alto: {data.get('height')}")
print(f"Meta de ingresos: {data.get('goal')}")

# Continuar con la inicialización de Pygame
pygame.init()

# CORRECCIÓN: Usar los datos de 'data'
TILE_SIZE = 30
screen_width = data.get('width', 20) * TILE_SIZE
screen_height = data.get('height', 20) * TILE_SIZE
screen = pygame.display.set_mode((screen_width, screen_height))

# Título de la ventana
pygame.display.set_caption("Courier Quest")

# Definir colores (FUERA DEL BUCLE)
BLACK = (0, 0, 0)
TILE_COLORS = {
    "C": (100, 100, 100),  # Calles (gris)
    "P": (50, 200, 50),    # Parques (verde)
    "B": (50, 50, 50),     # Edificios (gris oscuro)
}

# ----------------------------------------------
# Lógica para la imagen y el movimiento
# ----------------------------------------------

# Cargar la imagen del repartidor desde la ruta especificada
try:
    courier_image = pygame.image.load(os.path.join("images", "repartidor.png")).convert_alpha()
    # Escalar la imagen al tamaño de la celda del mapa
    courier_image = pygame.transform.scale(courier_image, (TILE_SIZE, TILE_SIZE))
except pygame.error as e:
    print(f"Error al cargar la imagen: {e}")
    courier_image = None # Establece la imagen a None en caso de error

# Crear la instancia del repartidor con la imagen
courier = Courier(start_x=0, start_y=0, image=courier_image)

# El bucle principal del juego
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Manejar el movimiento del jugador con las teclas
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                courier.move(0, -1)
            elif event.key == pygame.K_DOWN:
                courier.move(0, 1)
            elif event.key == pygame.K_LEFT:
                courier.move(-1, 0)
            elif event.key == pygame.K_RIGHT:
                courier.move(1, 0)
    
    screen.fill(BLACK)

    map_tiles = data.get('tiles', [])
    if map_tiles:
        for y, row in enumerate(map_tiles):
            for x, tile_type in enumerate(row):
                color = TILE_COLORS.get(tile_type, (255, 255, 255))
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, color, rect, 0)

    # Dibujar al repartidor si la imagen se cargó correctamente
    if courier_image:
        courier.draw(screen, TILE_SIZE)
    else:
        # Si no hay imagen, dibuja un círculo para depuración
        pygame.draw.circle(screen, (255, 0, 0), (courier.x * TILE_SIZE + TILE_SIZE // 2, courier.y * TILE_SIZE + TILE_SIZE // 2), TILE_SIZE // 2)

    pygame.display.flip()

pygame.quit()
"""

import pygame
import os
from api.api_handler import get_map_data, get_jobs_data, get_weather_data
from courier_quest.src.game.courier import Courier

# Obtener los datos del mapa al inicio del programa
map_data = get_map_data()
jobs_data = get_jobs_data()
weather_data = get_weather_data()

# Si los datos no se pudieron cargar, sal del programa
if not map_data:
    print("No se pudo cargar el mapa. Saliendo del juego.")
    pygame.quit()
    exit()

# CORRECCIÓN: Acceder a los datos dentro de 'data'
data = map_data.get('data', {})

# Ahora, puedes acceder a los datos del mapa
print("--- Detalles del Mapa ---")
print(f"Versión: {map_data.get('version')}")
print(f"Ancho: {data.get('width')}")
print(f"Alto: {data.get('height')}")
print(f"Meta de ingresos: {data.get('goal')}")

# Continuar con la inicialización de Pygame
pygame.init()

# CORRECCIÓN: Usar los datos de 'data'
TILE_SIZE = 30
screen_width = data.get('width', 20) * TILE_SIZE
screen_height = data.get('height', 20) * TILE_SIZE
screen = pygame.display.set_mode((screen_width, screen_height))

# Título de la ventana
pygame.display.set_caption("Courier Quest")

# Definir colores (FUERA DEL BUCLE)
BLACK = (0, 0, 0)
TILE_COLORS = {
    "C": (100, 100, 100),  # Calles (gris)
    "P": (50, 200, 50),    # Parques (verde)
    "B": (50, 50, 50),     # Edificios (gris oscuro)
}

# ----------------------------------------------
# Lógica para la imagen y el movimiento
# ----------------------------------------------

# Cargar la imagen del repartidor desde la ruta especificada
try:
    courier_image = pygame.image.load(os.path.join("images", "repartidor.png")).convert_alpha()
    # Escalar la imagen al tamaño de la celda del mapa
    courier_image = pygame.transform.scale(courier_image, (TILE_SIZE, TILE_SIZE))
except pygame.error as e:
    print(f"Error al cargar la imagen del repartidor: {e}")
    courier_image = None # Establece la imagen a None en caso de error

# ----------------------------------------------
# Cargar la imagen del edificio
# ----------------------------------------------
try:
    building_image = pygame.image.load(os.path.join("images", "edificio.png")).convert_alpha()
    building_image = pygame.transform.scale(building_image, (TILE_SIZE, TILE_SIZE))
except pygame.error as e:
    print(f"Error al cargar la imagen del edificio: {e}")
    building_image = None

# Crear la instancia del repartidor con la imagen
courier = Courier(start_x=0, start_y=0, image=courier_image)

# El bucle principal del juego
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Manejar el movimiento del jugador con las teclas
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                courier.move(0, -1)
            elif event.key == pygame.K_DOWN:
                courier.move(0, 1)
            elif event.key == pygame.K_LEFT:
                courier.move(-1, 0)
            elif event.key == pygame.K_RIGHT:
                courier.move(1, 0)
    
    screen.fill(BLACK)

    map_tiles = data.get('tiles', [])
    if map_tiles:
        for y, row in enumerate(map_tiles):
            for x, tile_type in enumerate(row):
                # Posición del tile en píxeles
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

                if tile_type == "B" and building_image:
                    # Dibuja la imagen del edificio si la imagen se cargó
                    screen.blit(building_image, rect)
                else:
                    # Dibuja el color del tile para calles y parques
                    color = TILE_COLORS.get(tile_type, (255, 255, 255))
                    pygame.draw.rect(screen, color, rect, 0)

    # Dibujar al repartidor si la imagen se cargó correctamente
    if courier_image:
        courier.draw(screen, TILE_SIZE)
    else:
        # Si no hay imagen, dibuja un círculo para depuración
        pygame.draw.circle(screen, (255, 0, 0), (courier.x * TILE_SIZE + TILE_SIZE // 2, courier.y * TILE_SIZE + TILE_SIZE // 2), TILE_SIZE // 2)

    pygame.display.flip()

pygame.quit()
