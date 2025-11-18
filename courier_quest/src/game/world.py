"""
Módulo de representación del mundo (mapa) en Courier Quest

Usa pygame para dibujar el mapa (calles, pasto, edificios)
`TILE_COLORS` define colores por tipo de tile cuando no hay imagen
`TILE_SIZE` define el tamaño de cada tile en píxeles
imoprt random para seleccionar imágenes aleatorias de edificios
"""
import pygame
from game.palette import TILE_COLORS
from game.constants import TILE_SIZE
import random


class World:
    """
    Representa el mapa del juego como una cuadrícula de tiles.

    Se encarga de:
      - Guardar la información del mapa (tiles, tamaño, leyenda).
      - Dibujar el suelo (calles, parques) y los edificios.
      - Proveer utilidades para pathfinding y lógica de juego
        (walkable, surface_weight, posiciones de calles, etc.).
    """

    def __init__(self, map_data, building_images=None, grass_image=None, street_images=None):
        """
        Inicializa el mundo a partir de los datos del mapa.

        Parameters
        ----------
        map_data : dict
            Diccionario con la estructura del mapa. Se espera que contenga
            una clave 'data' con:
              - 'tiles': matriz de caracteres ('C', 'P', 'B', etc.)
              - 'width': ancho del mapa en tiles
              - 'height': alto del mapa en tiles
              - 'legend': (opcional) metadatos por tipo de tile, incluyendo
                          'surface_weight'.
        building_images : dict[(int,int), pygame.Surface], opcional
            Mapa de tamaños de bloques de edificios (ancho, alto) a imágenes
            pre-cargadas para dibujarlos en una sola pieza.
        grass_image : pygame.Surface, opcional
            Imagen a usar para tiles de tipo 'P' (parque/pasto). Si es None,
            se dibuja con un color sólido.
        street_images : dict[str, pygame.Surface], opcional
            Imágenes para las calles. Se usa la clave "patron_base" para
            dibujar el patrón base de las calles si está disponible.
        """
        self.map_data = map_data.get('data', {})
        self.tiles = self.map_data.get('tiles', [])
        self.width = self.map_data.get('width', 0)
        self.height = self.map_data.get('height', 0)
        self.building_images = building_images if building_images else {}
        self.grass_image = grass_image

        self.street_images = street_images if street_images else {}

    def get_building_size(self, start_x, start_y, visited):
        """
        Calcula el tamaño de un bloque de edificios contiguo (tile 'B').

        Recorre en ancho y alto todos los tiles 'B' conectados (4 vecinos)
        a partir de (start_x, start_y), marcándolos como visitados para que
        no se vuelvan a procesar.

        Parameters
        ----------
        start_x : int
            Coordenada x del tile inicial (en índices de grid).
        start_y : int
            Coordenada y del tile inicial (en índices de grid).
        visited : set[(int,int)]
            Conjunto de coordenadas (x, y) de tiles de edificios ya
            procesados.

        Returns
        -------
        block_width : int
            Ancho del bloque de edificios en número de tiles.
        block_height : int
            Alto del bloque de edificios en número de tiles.
        (min_x, min_y) : tuple[int, int]
            Coordenada superior izquierda del bloque (en tiles).
        """
        if start_x >= self.width or start_y >= self.height or self.tiles[start_y][start_x] != "B" or (start_x, start_y) in visited:
            return 0, 0, (start_x, start_y)

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
        """
        Dibuja el mapa completo en la superficie dada.

        Primero dibuja el suelo (calles y parques) y luego, en una segunda
        pasada, dibuja los bloques de edificios escalando las imágenes
        correspondientes o, en su defecto, usando rectángulos de color.

        Parameters
        ----------
        screen : pygame.Surface
            Superficie sobre la que se dibuja el mundo (normalmente la
            ventana principal del juego).
        """
        visited_buildings = set()

        # PASS 1: DIBUJAR SUELO
        street_image_to_use = self.street_images.get("patron_base")

        for y in range(self.height):
            for x in range(self.width):
                tile_type = self.tiles[y][x]

                if tile_type == "C":
                    if street_image_to_use:
                        screen.blit(street_image_to_use, (x * TILE_SIZE, y * TILE_SIZE))
                    else:
                        color = TILE_COLORS.get(tile_type, (100, 100, 100))
                        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        pygame.draw.rect(screen, color, rect)

                elif tile_type == "P":
                    if self.grass_image:
                        screen.blit(self.grass_image, (x * TILE_SIZE, y * TILE_SIZE))
                    else:
                        color = TILE_COLORS.get(tile_type, (50, 200, 50))
                        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        pygame.draw.rect(screen, color, rect)

        # PASS 2: DIBUJAR EDIFICIOS
        for y in range(self.height):
            for x in range(self.width):
                tile_type = self.tiles[y][x]

                if tile_type == "B" and (x, y) not in visited_buildings:
                    block_width, block_height, (start_x, start_y) = self.get_building_size(x, y, visited_buildings)

                    if block_width > 0 and block_height > 0:
                        image = self.building_images.get((block_width, block_height))

                        if image:
                            scaled_image = pygame.transform.scale(image, (block_width * TILE_SIZE, block_height * TILE_SIZE))
                            screen.blit(scaled_image, (start_x * TILE_SIZE, start_y * TILE_SIZE))
                        else:
                            rect = pygame.Rect(start_x * TILE_SIZE, start_y * TILE_SIZE,
                                               block_width * TILE_SIZE, block_height * TILE_SIZE)
                            pygame.draw.rect(screen, TILE_COLORS.get("B", (50, 50, 50)), rect, 0)

    # ---------- DEBUG VISUAL: RUTA IA ----------
    def draw_ai_path(self, screen, path, color=(0, 255, 255)):
        """
        Dibuja la ruta planificada de la IA sobre el mapa.

        Parameters
        ----------
        screen : pygame.Surface
            Superficie donde se dibuja la ruta.
        path : list[tuple[int, int]]
            Lista de posiciones (x, y) en coordenadas de tiles que conforman
            el camino calculado (por ejemplo, por A*).
        color : tuple[int, int, int], opcional
            Color base para la línea y los nodos de la ruta.

        Detalles
        --------
        - Dibuja:
          * una línea que conecta todos los nodos
          * pequeños círculos en cada nodo
          * un nodo inicial y final resaltados con colores distintos
        """
        if not path or len(path) == 0:
            return

        # Convertir tiles a píxeles (centro del tile)
        points = []
        for (tx, ty) in path:
            if 0 <= tx < self.width and 0 <= ty < self.height:
                cx = tx * TILE_SIZE + TILE_SIZE // 2
                cy = ty * TILE_SIZE + TILE_SIZE // 2
                points.append((cx, cy))

        if len(points) < 2:
            # si solo hay un punto, dibujamos solo el nodo
            cx, cy = points[0]
            pygame.draw.circle(screen, color, (cx, cy), 6, 2)
            return

        # Línea principal
        pygame.draw.lines(screen, color, False, points, 3)

        # Nodos intermedios
        for px, py in points:
            pygame.draw.circle(screen, color, (px, py), 4, 1)

        # Inicio (cerca de la IA) – color distinto
        start_x, start_y = points[0]
        pygame.draw.circle(screen, (0, 200, 0), (start_x, start_y), 6, 2)

        # Destino – resaltado en otro color
        end_x, end_y = points[-1]
        pygame.draw.circle(screen, (255, 200, 0), (end_x, end_y), 6, 2)

    def is_walkable(self, x, y):
        """
        Indica si un tile en (x, y) es transitable para el courier.

        Parameters
        ----------
        x : int
            Coordenada x en tiles.
        y : int
            Coordenada y en tiles.

        Returns
        -------
        bool
            True si el tile está dentro de los límites del mapa y no es
            un edificio ('B'); False en caso contrario.
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        tile_type = self.tiles[y][x]
        return tile_type != "B"

    def surface_weight_at(self, x, y):
        """
        Retorna el 'surface_weight' del tipo de tile en (x, y).

        El 'surface_weight' se usa para ajustar el coste de movimiento en el
        pathfinding (por ejemplo, calles más rápidas, zonas más lentas, etc.).

        Parameters
        ----------
        x : int
            Coordenada x en tiles.
        y : int
            Coordenada y en tiles.

        Returns
        -------
        float
            Valor de 'surface_weight' definido en la leyenda del mapa para
            el tipo de tile correspondiente. Si no hay dato o está fuera
            de rango, devuelve 1.0 por defecto.
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return 1.0

        tile_type = self.tiles[y][x]

        legend = self.map_data.get('legend', {})
        weight = legend.get(tile_type, {}).get('surface_weight', 1.0)
        return weight

    def get_building_edges(self):
        """
        Retorna todas las posiciones de tiles adyacentes a edificios.

        Se consideran "bordes" aquellos tiles que:
          - No son edificios ('B').
          - No son parques ('P').
          - Están en las 4 direcciones cardinales alrededor de un edificio.

        Returns
        -------
        list[tuple[int, int]]
            Lista de coordenadas (x, y) de tiles adyacentes a bloques de
            edificios. Son candidatos típicos para colocar pickups/dropoffs.
        """
        edges = set()

        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == "B":
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < self.width and 0 <= ny < self.height and
                            self.tiles[ny][nx] != "B" and
                            self.tiles[ny][nx] != "P"):
                            edges.add((nx, ny))

        return list(edges)

    def get_street_positions(self):
        """
        Retorna todas las posiciones de calles válidas para pedidos.

        Busca en la matriz de tiles aquellos marcados como 'C' (calle) y
        devuelve sus coordenadas en tiles.

        Returns
        -------
        list[tuple[int, int]]
            Lista de coordenadas (x, y) de tiles de tipo 'C' donde pueden
            generarse pickups o dropoffs.
        """
        streets = []
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == "C":
                    streets.append((x, y))
        return streets
