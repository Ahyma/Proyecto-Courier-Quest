import pygame
from game.palette import TILE_COLORS
from game.constants import TILE_SIZE

class World:
    def __init__(self, map_data):
        self.map_data = map_data.get('data', {})
        self.tiles = self.map_data.get('tiles', [])
        self.width = self.map_data.get('width', 0)
        self.height = self.map_data.get('height', 0)

    def draw(self, screen):
        """
        Dibuja el mundo del juego en la pantalla.
        """
        for y, row in enumerate(self.tiles):
            for x, tile_type in enumerate(row):
                color = TILE_COLORS.get(tile_type, (255, 255, 255))
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, color, rect, 0)

    def is_walkable(self, x, y):
        """
        Verifica si una coordenada es un tile transitable.
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        tile_type = self.tiles[y][x]
        # Por ahora, solo los edificios son intransitables
        return tile_type != "B"