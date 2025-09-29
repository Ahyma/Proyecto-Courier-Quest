import pygame
from .palette import TILE_COLORS
from .constants import TILE_SIZE as DEFAULT_TILE_SIZE

class World:
    def __init__(self, map_data, building_images=None, grass_image=None, street_images=None):
        # Normaliza el contenedor del mapa
        self.map_data = map_data.get('data', {}) if isinstance(map_data, dict) else (map_data or {})
        self.tiles  = self.map_data.get('tiles', [])
        self.width  = self.map_data.get('width', 0)
        self.height = self.map_data.get('height', 0)

        # Recursos
        self.building_images = building_images if building_images else {}
        self.grass_image  = grass_image
        self.street_images = street_images if street_images else {}

    # ---------------- helpers ----------------
    def _blit_tile(self, screen, img, x, y, ts):
        if img is None:
            return
        if img.get_width() != ts or img.get_height() != ts:
            img = pygame.transform.scale(img, (ts, ts))
        screen.blit(img, (x * ts, y * ts))

    def _draw_cloud(self, screen, x, y, ts):
        # Nube vectorial simple (por si usas el tile 'N')
        cx, cy = x * ts, y * ts
        c = (235, 245, 255)
        pygame.draw.ellipse(screen, c, pygame.Rect(cx + ts*0.10, cy + ts*0.40, ts*0.55, ts*0.35))
        pygame.draw.ellipse(screen, c, pygame.Rect(cx + ts*0.35, cy + ts*0.30, ts*0.55, ts*0.45))
        pygame.draw.ellipse(screen, c, pygame.Rect(cx + ts*0.20, cy + ts*0.35, ts*0.60, ts*0.40))

    def _nearest_building_image(self, size_xy):
        """
        Devuelve la imagen de edificio más parecida al tamaño solicitado.
        Primero minimiza la diferencia de área; si hay empate, el menor error en lados.
        """
        if not self.building_images:
            return None
        W, H = size_xy
        target_area = W * H

        best_img = None
        best_key = None
        best = (float("inf"), float("inf"))  # (diff_area, diff_sides)

        for (w, h), img in self.building_images.items():
            if img is None:
                continue
            diff_area = abs((w * h) - target_area)
            diff_sides = abs(w - W) + abs(h - H)
            key = (diff_area, diff_sides)
            if key < best:
                best = key
                best_key = (w, h)
                best_img = img

        return best_img

    # ------------- edificios ------------------
    def get_building_size(self, start_x, start_y, visited):
        if (
            start_x >= self.width or start_y >= self.height
            or self.tiles[start_y][start_x] != "B"
            or (start_x, start_y) in visited
        ):
            return 0, 0, (start_x, start_y)

        queue = [(start_x, start_y)]
        visited.add((start_x, start_y))
        min_x = max_x = start_x
        min_y = max_y = start_y

        while queue:
            x, y = queue.pop(0)
            min_x = min(min_x, x); max_x = max(max_x, x)
            min_y = min(min_y, y); max_y = max(max_y, y)

            for dx, dy in [(1,0),(0,1),(-1,0),(0,-1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height
                        and self.tiles[ny][nx] == "B"
                        and (nx, ny) not in visited):
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        return (max_x - min_x + 1), (max_y - min_y + 1), (min_x, min_y)

    # ------------- calles (autotile + fallbacks) -------------
    def get_street_image(self, x, y):
        up_t    = self.tiles[y-1][x] if y > 0 else None
        down_t  = self.tiles[y+1][x] if y < self.height - 1 else None
        left_t  = self.tiles[y][x-1] if x > 0 else None
        right_t = self.tiles[y][x+1] if x < self.width - 1 else None

        up, down = (up_t == "C"), (down_t == "C")
        left, right = (left_t == "C"), (right_t == "C")

        if up and down and left and right:
            img = self.street_images.get("centro")
            if img: return img

        if (up + down + left + right) == 3:
            img = self.street_images.get("centro")
            if img: return img

        if not up and not down and left and right:
            return self.street_images.get("horizontal") or self.street_images.get("default")
        if up and down and not left and not right:
            return self.street_images.get("vertical") or self.street_images.get("default")

        if not up and not down and not left and right:
            return self.street_images.get("borde_izquierda") or self.street_images.get("horizontal") or self.street_images.get("default")
        if not up and not down and left and not right:
            return self.street_images.get("borde_derecha") or self.street_images.get("horizontal") or self.street_images.get("default")
        if not up and down and not left and not right:
            return self.street_images.get("borde_arriba") or self.street_images.get("vertical") or self.street_images.get("default")
        if up and not down and not left and not right:
            return self.street_images.get("borde_abajo") or self.street_images.get("vertical") or self.street_images.get("default")

        if not up and down and left and not right:
            return self.street_images.get("esquina_arriba_derecha") or self.street_images.get("centro") or self.street_images.get("default")
        if not up and down and not left and right:
            return self.street_images.get("esquina_arriba_izquierda") or self.street_images.get("centro") or self.street_images.get("default")
        if up and not down and left and not right:
            return self.street_images.get("esquina_abajo_derecha") or self.street_images.get("centro") or self.street_images.get("default")
        if up and not down and not left and right:
            return self.street_images.get("esquina_abajo_izquierda") or self.street_images.get("centro") or self.street_images.get("default")

        return (self.street_images.get("centro")
                or self.street_images.get("horizontal")
                or self.street_images.get("vertical")
                or self.street_images.get("default"))

    # ---------------- render -----------------
    def draw(self, screen, tile_size: int | None = None):
        ts = tile_size or DEFAULT_TILE_SIZE

        # 1) Suelo base por color para evitar huecos
        for y, row in enumerate(self.tiles):
            for x, t in enumerate(row):
                base = TILE_COLORS.get(t)
                if base is not None:
                    pygame.draw.rect(screen, base, pygame.Rect(x*ts, y*ts, ts, ts), 0)

        # 2) Calles / parques / nubes
        for y, row in enumerate(self.tiles):
            for x, t in enumerate(row):
                if t == "C":
                    img = self.get_street_image(x, y)
                    if img:
                        self._blit_tile(screen, img, x, y, ts)
                elif t == "P":
                    if self.grass_image:
                        self._blit_tile(screen, self.grass_image, x, y, ts)
                elif t == "N":
                    self._draw_cloud(screen, x, y, ts)

        # 3) Edificios por bloque contiguo
        visited = set()
        for y, row in enumerate(self.tiles):
            for x, t in enumerate(row):
                if t == "B" and (x, y) not in visited:
                    bw, bh, (sx, sy) = self.get_building_size(x, y, visited)
                    if bw > 0 and bh > 0:
                        # Imagen exacta o más parecida
                        img = self.building_images.get((bw, bh)) or self._nearest_building_image((bw, bh))
                        if img:
                            scaled = pygame.transform.scale(img, (bw*ts, bh*ts))
                            screen.blit(scaled, (sx*ts, sy*ts))
                        else:
                            # Fallback último recurso (raro)
                            pygame.draw.rect(screen, (100,100,100),
                                             pygame.Rect(sx*ts, sy*ts, bw*ts, bh*ts), 0)

    # ------------- lógica de colisiones / terreno -------------
    def is_walkable(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.tiles[y][x] != "B"

    def surface_weight_at(self, x, y):
        legend = self.map_data.get("legend", {}) if hasattr(self, "map_data") else {}
        try:
            t = self.tiles[y][x]
            return float(legend.get(t, {}).get("surface_weight", 1.0))
        except Exception:
            return 1.0
