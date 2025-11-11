import pygame
from game.palette import TILE_COLORS
from game.constants import TILE_SIZE
import random 

class World:
    """
    Representa el mundo del juego con su mapa y elementos visuales.
    
    Responsabilidades:
    - Cargar y gestionar el mapa desde datos
    - Dibujar el mundo (edificios, calles, césped)
    - Verificar transitabilidad de posiciones
    - Proporcionar información sobre superficies
    """
    
    def __init__(self, map_data, building_images=None, grass_image=None, street_images=None):
        """
        Inicializa el mundo del juego.
        
        Args:
            map_data: Datos del mapa (tiles, dimensiones, leyenda)
            building_images: Imágenes para diferentes tamaños de edificios
            grass_image: Imagen para césped/parques
            street_images: Imágenes para calles
        """
        self.map_data = map_data.get('data', {})
        self.tiles = self.map_data.get('tiles', [])  # Matriz de tiles
        self.width = self.map_data.get('width', 0)   # Ancho en tiles
        self.height = self.map_data.get('height', 0) # Alto en tiles
        self.building_images = building_images if building_images else {}
        self.grass_image = grass_image
        self.street_images = street_images if street_images else {}
        
    def get_building_size(self, start_x, start_y, visited):
        """
        Calcula el tamaño de un bloque de edificios contiguo usando BFS.
        
        Args:
            start_x, start_y: Posición inicial para buscar
            visited: Conjunto de posiciones ya visitadas
            
        Returns:
            Tupla (ancho, alto, (x_inicio, y_inicio)) del bloque
        """
        # Verificar si la posición es válida y es un edificio no visitado
        if start_x >= self.width or start_y >= self.height or self.tiles[start_y][start_x] != "B" or (start_x, start_y) in visited:
            return 0, 0, (start_x, start_y)

        # Búsqueda en amplitud para encontrar todos los tiles conectados
        queue = [(start_x, start_y)]
        visited.add((start_x, start_y))
        
        # Seguimiento de límites del bloque
        min_x, max_x = start_x, start_x
        min_y, max_y = start_y, start_y
        
        while queue:
            x, y = queue.pop(0)
            
            # Actualizar límites
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            
            # Explorar vecinos (arriba, abajo, izquierda, derecha)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                # Verificar si el vecino es un edificio no visitado
                if (0 <= nx < self.width and 
                    0 <= ny < self.height and 
                    self.tiles[ny][nx] == "B" and 
                    (nx, ny) not in visited):
                    
                    visited.add((nx, ny))
                    queue.append((nx, ny))
                    
        # Calcular dimensiones del bloque
        block_width = max_x - min_x + 1
        block_height = max_y - min_y + 1
        
        return block_width, block_height, (min_x, min_y)

    def draw(self, screen):
        """
        Dibuja todo el mundo en la pantalla.
        
        Proceso en dos pasos:
        1. Dibujar suelo (calles y césped)
        2. Dibujar edificios como bloques unificados
        """
        visited_buildings = set()  # Para evitar redibujar edificios
        
        # PASS 1: DIBUJAR SUELO (calles y césped)
        street_image_to_use = self.street_images.get("patron_base")
        
        for y in range(self.height):
            for x in range(self.width):
                tile_type = self.tiles[y][x]
                
                if tile_type == "C":  # Calle
                    if street_image_to_use:
                        # Usar imagen de calle si está disponible
                        screen.blit(street_image_to_use, (x * TILE_SIZE, y * TILE_SIZE)) 
                    else:
                        # Fallback: color sólido
                        color = TILE_COLORS.get(tile_type, (100, 100, 100)) 
                        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        pygame.draw.rect(screen, color, rect)
                
                elif tile_type == "P":  # Parque/césped
                    if self.grass_image:
                        # Usar imagen de césped si está disponible
                        screen.blit(self.grass_image, (x * TILE_SIZE, y * TILE_SIZE))
                    else:
                        # Fallback: color verde
                        color = TILE_COLORS.get(tile_type, (50, 200, 50)) 
                        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        pygame.draw.rect(screen, color, rect)
                
        # PASS 2: DIBUJAR EDIFICIOS como bloques unificados
        for y in range(self.height):
            for x in range(self.width):
                tile_type = self.tiles[y][x]
                
                # Si es un edificio no visitado, dibujar todo el bloque
                if tile_type == "B" and (x, y) not in visited_buildings:
                    block_width, block_height, (start_x, start_y) = self.get_building_size(x, y, visited_buildings)
                    
                    if block_width > 0 and block_height > 0:
                        # Buscar imagen para este tamaño de bloque
                        image = self.building_images.get((block_width, block_height))
                        
                        if image:
                            # Escalar y dibujar imagen del edificio
                            scaled_image = pygame.transform.scale(image, (block_width * TILE_SIZE, block_height * TILE_SIZE))
                            screen.blit(scaled_image, (start_x * TILE_SIZE, start_y * TILE_SIZE))
                        else:
                            # Fallback: rectángulo sólido
                            rect = pygame.Rect(start_x * TILE_SIZE, start_y * TILE_SIZE, block_width * TILE_SIZE, block_height * TILE_SIZE)
                            pygame.draw.rect(screen, TILE_COLORS.get("B", (50, 50, 50)), rect, 0)
                            
    def is_walkable(self, x, y):
        """
        Verifica si una posición es transitable.
        
        Returns:
            True si la posición está dentro del mapa y no es un edificio
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False  # Fuera de los límites
        tile_type = self.tiles[y][x]
        return tile_type != "B"  # No edificio
       
    def get_adjacent_walkable_cells(self, x, y):
        """
        Retorna una lista de tuplas (x, y) de celdas adyacentes transitables.
        
        Utilizado por la IA para determinar los movimientos posibles, asegurando
        que no intenten moverse hacia edificios o fuera del mapa.

        Args:
            x, y: Posición actual del courier.
            
        Returns:
            Lista de posiciones (x, y) transitables adyacentes.
        """
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)] # Norte, Sur, Este, Oeste
        walkable_cells = []
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            # Reutiliza el método existente para verificar límites y transitabilidad
            if self.is_walkable(nx, ny): 
                walkable_cells.append((nx, ny))
                
        return walkable_cells

    def surface_weight_at(self, x, y):
        """
        Obtiene el peso de la superficie en una posición.
        
        El peso afecta la velocidad de movimiento:
        - 1.0 = velocidad normal (Calle)
        - <1.0 = más lento (Césped)
        
        Returns:
            Multiplicador de velocidad para la superficie
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 1.0  # Fuera de límites = normal

        tile_type = self.tiles[y][x]
        
        # DEFINICIÓN MANUAL DE PESOS para asegurar la penalización del pasto/parque
        if tile_type == "C": # Calle: Velocidad normal
            weight = 1.0
        elif tile_type == "P": # Parque/Césped: 50% más lento (ej: peso de 0.66 hace que 1.0/0.66 = ~1.5)
            weight = 0.66 
        elif tile_type == "B": # Edificio: Nunca se debería llegar aquí si is_walkable funciona, pero por si acaso.
            weight = 0.001 
        else: # Otros (por defecto, como la calle)
            weight = 1.0 
            
        return weight

    def get_building_edges(self):
        """
        Encuentra todas las posiciones adyacentes a edificios.
        
        Útil para generar puntos de recogida de pedidos.
        
        Returns:
            Lista de posiciones (x, y) adyacentes a edificios
        """
        edges = set()
        
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == "B":  # Es un edificio
                    # Revisar los 4 vecinos
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        # Si el vecino es transitable y no es parque, es un borde válido
                        if (0 <= nx < self.width and 0 <= ny < self.height and 
                            self.tiles[ny][nx] != "B" and 
                            self.tiles[ny][nx] != "P"):
                            edges.add((nx, ny))
        
        return list(edges)

    def get_street_positions(self):
        """
        Obtiene todas las posiciones de calles en el mapa.
        
        Returns:
            Lista de posiciones (x, y) que son calles
        """
        streets = []
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == "C":  # Calle
                    streets.append((x, y))
        return streets
    
    def is_resting_spot(self, x: int, y: int) -> bool:
        """
        Verifica si una posición (x, y) es una celda de descanso.
        
        Las celdas de descanso se definen como "Parque/césped" (tipo de tile "P").
        """
        # Verificar si las coordenadas están dentro de los límites
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False 
        
        # El tipo de tile para Parques/Césped es "P" (según tu método draw)
        tile_type = self.tiles[y][x] 
        return tile_type == "P"