import pygame
from game.palette import TILE_COLORS
from game.constants import TILE_SIZE
import random 

class World:
    def __init__(self, map_data, building_images=None, grass_image=None, street_images=None):
        self.map_data = map_data.get('data', {})
        self.tiles = self.map_data.get('tiles', [])
        self.width = self.map_data.get('width', 0)
        self.height = self.map_data.get('height', 0)
        self.building_images = building_images if building_images else {}
        self.grass_image = grass_image
        
        # street_images ahora solo contiene {"patron_base": imagen_escalada o None}
        self.street_images = street_images if street_images else {}
        
    def get_building_size(self, start_x, start_y, visited):
        """
        Calcula el tamaño de un bloque de edificios contiguo (B).
        Retorna el ancho y el alto del bloque, y la coordenada inicial (esquina superior izquierda).
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
            
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (0 <= nx < self.width and 
                    0 <= ny < self.height and 
                    self.tiles[ny][nx] == "B" and 
                    (nx, ny) not in visited):
                    
                    visited.add((nx, ny))
                    queue.append((nx, ny))
                    
        block_width = max_x - min_x + 1
        block_height = max_y - min_y + 1
        
        return block_width, block_height, (min_x, min_y)

    def draw(self, screen):
        visited_buildings = set()
        
        # === PASS 1: DIBUJAR TODO EL SUELO (CALLES Y PARQUES) ===
        # Obtenemos la imagen UNA SOLA VEZ del diccionario, puede ser None
        street_image_to_use = self.street_images.get("patron_base")
        
        for y in range(self.height):
            for x in range(self.width):
                tile_type = self.tiles[y][x]
                
                # Dibuja Calles 'C'
                if tile_type == "C": 
                    # Verificar si la imagen se cargó correctamente (para evitar el 'NoneType' error)
                    if street_image_to_use:
                        screen.blit(street_image_to_use, (x * TILE_SIZE, y * TILE_SIZE)) 
                    else:
                        # Fallback: color gris de calle
                        color = TILE_COLORS.get(tile_type, (100, 100, 100)) 
                        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        pygame.draw.rect(screen, color, rect)
                
                # Dibuja Parques/Césped 'P'
                elif tile_type == "P": 
                    if self.grass_image:
                        screen.blit(self.grass_image, (x * TILE_SIZE, y * TILE_SIZE))
                    else:
                        # Fallback: color verde de parque
                        color = TILE_COLORS.get(tile_type, (50, 200, 50)) 
                        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        pygame.draw.rect(screen, color, rect)
                
        # === PASS 2: DIBUJAR EDIFICIOS ('B' blocks) ===
        for y in range(self.height):
            for x in range(self.width):
                tile_type = self.tiles[y][x]
                
                if tile_type == "B" and (x, y) not in visited_buildings:
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
                            # Fallback: Dibuja un rectángulo de color para el edificio
                            rect = pygame.Rect(start_x * TILE_SIZE, start_y * TILE_SIZE, block_width * TILE_SIZE, block_height * TILE_SIZE)
                            pygame.draw.rect(screen, TILE_COLORS.get("B", (50, 50, 50)), rect, 0)
                            
    def is_walkable(self, x, y):
        """
        Verifica si una coordenada es un tile transitable.
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        tile_type = self.tiles[y][x]
        return tile_type != "B"
       
    def surface_weight_at(self, x, y):
        """
        Retorna el 'surface_weight' del tipo de tile en (x, y). 
        Este valor es un multiplicador de costo/velocidad para el movimiento.
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 1.0 # Peso por defecto para fuera del mapa

        tile_type = self.tiles[y][x]
        
        # Obtiene la leyenda completa del mapa
        legend = self.map_data.get('legend', {})
        
        # Busca el peso en la leyenda, o usa 1.0 por defecto
        weight = legend.get(tile_type, {}).get('surface_weight', 1.0)
        return weight