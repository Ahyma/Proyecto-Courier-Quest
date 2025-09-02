#es nuestro main
"""
import pygame
 
pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("Test Pygame")
 
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
 
pygame.quit()
"""

import pygame
from api.api_handler import get_map_data

# Obtener los datos del mapa al inicio del programa
map_data = get_map_data()

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
screen_width = data.get('width', 20) * 30  # 30 píxeles por celda (ejemplo)
screen_height = data.get('height', 20) * 30

screen = pygame.display.set_mode((screen_width, screen_height))

# Título de la ventana
pygame.display.set_caption("Courier Quest")

# Definir colores
BLACK = (0, 0, 0)

# El bucle principal del juego
running = True
while running:
    #for event in pygame.event.get():
    #    if event.type == pygame.QUIT:
    #        running = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)
    pygame.display.flip()

pygame.quit()
