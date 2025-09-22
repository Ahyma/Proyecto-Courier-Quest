import pygame
from game.palette import TILE_COLORS
from game.constants import TILE_SIZE

class World:
    def __init__(self, map_data, building_images=None, grass_image=None, street_image=None):
        self.map_data = map_data.get('data', {})
        self.tiles = self.map_data.get('tiles', [])
        self.width = self.map_data.get('width', 0)
        self.height = self.map_data.get('height', 0)
        self.building_images = building_images if building_images else {}
        self.grass_image = grass_image
        self.street_image = street_image
        
    def get_building_size(self, start_x, start_y, visited):
        """
        Calcula el tamaño de un bloque de edificios contiguo.
        Retorna el ancho y el alto del bloque.
        """
        if start_x >= self.width or start_y >= self.height or self.tiles[start_y][start_x] != "B" or (start_x, start_y) in visited:
            return 0, 0, (start_x, start_y)

        # Usar una cola para una búsqueda de anchura (BFS)
        queue = [(start_x, start_y)]
        visited.add((start_x, start_y))
        
        min_x, max_x = start_x, start_x
        min_y, max_y = start_y, start_y
        
        while queue:
            x, y = queue.pop(0)
            
            # Actualiza las dimensiones del bloque
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

            # Revisa los vecinos (derecha, abajo, izquierda, arriba)
            for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                nx, ny = x + dx, y + dy
                
                if 0 <= nx < self.width and 0 <= ny < self.height and self.tiles[ny][nx] == "B" and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        
        width = (max_x - min_x) + 1
        height = (max_y - min_y) + 1
        
        # Devuelve el tamaño y la esquina superior izquierda
        return width, height, (min_x, min_y)

    def draw(self, screen):
        """
        Dibuja el mundo del juego, usando imágenes para cada tipo de tile.
        """
        visited_buildings = set()
        
        for y, row in enumerate(self.tiles):
            for x, tile_type in enumerate(row):
                if tile_type == "C":  # Si es calle
                    if self.street_image:
                        screen.blit(self.street_image, (x * TILE_SIZE, y * TILE_SIZE))
                    else:
                        color = TILE_COLORS.get(tile_type, (255, 255, 255))
                        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        pygame.draw.rect(screen, color, rect, 0)
                elif tile_type == "P":  # Si es parque
                    if self.grass_image:
                        screen.blit(self.grass_image, (x * TILE_SIZE, y * TILE_SIZE))
                    else:
                        color = TILE_COLORS.get(tile_type, (255, 255, 255))
                        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        pygame.draw.rect(screen, color, rect, 0)
                
                elif tile_type == "B" and (x, y) not in visited_buildings:
                    # Si es un edificio no visitado, calcula su tamaño
                    block_width, block_height, (start_x, start_y) = self.get_building_size(x, y, visited_buildings)
                    
                    if block_width > 0 and block_height > 0:
                        # Selecciona la imagen correcta del diccionario
                        image = self.building_images.get((block_width, block_height))
                        
                        if image:
                            # Escala la imagen del edificio al tamaño del bloque y la dibuja
                            scaled_image = pygame.transform.scale(image, (block_width * TILE_SIZE, block_height * TILE_SIZE))
                            screen.blit(scaled_image, (start_x * TILE_SIZE, start_y * TILE_SIZE))
                        else:
                            # Dibuja un rectángulo de color si no hay imagen específica
                            rect = pygame.Rect(start_x * TILE_SIZE, start_y * TILE_SIZE, block_width * TILE_SIZE, block_height * TILE_SIZE)
                            pygame.draw.rect(screen, (100, 100, 100), rect, 0)
                            
    def is_walkable(self, x, y):
        """
        Verifica si una coordenada es un tile transitable.
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        tile_type = self.tiles[y][x]
        return tile_type != "B"