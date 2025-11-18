"""
import pygame es para manejar gráficos y efectos visuales
import os es para manejar rutas de archivos y directorios
import random es para selecciones aleatorias y temporizadores
"""
import pygame
import os
import random

# Rutas absolutas para las imágenes de clima (apunta a courier_quest/src/images)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "images"))


class WeatherVisuals:
    """
    Gestiona y dibuja los efectos visuales de clima sobre la pantalla.

    Usa la condición climática actual (ej. 'rain', 'fog', 'heat') y un parámetro
    de intensidad (0–1) para:
      - Crear y actualizar partículas (lluvia, nieve, viento, nubes).
      - Dibujar capas semitransparentes para niebla y calor.
    """
    def __init__(self, screen_size, tile_size):
        """
        Inicializa el sistema de efectos climáticos.

        Parameters
        ----------
        screen_size : tuple[int, int]
            Tamaño de la ventana de juego en píxeles, como (ancho, alto).
        tile_size : int
            Tamaño de cada tile en píxeles. Se usa para escalar las partículas
            relativas al mapa (gotas, copos, nubes, etc.).
        """
        self.screen_width, self.screen_height = screen_size
        self.tile_size = tile_size
        self.current_condition = "clear"
        self.intensity = 1.0  # por defecto

        # Partículas/superficies por condición
        self.effects = {
            "rain":       {"particles": [], "image": None},
            "rain_light": {"particles": [], "image": None},
            "storm":      {"particles": [], "image": None},
            "fog":        {"surface": None, "alpha": 0},
            "wind":       {"particles": [], "image": None},
            "heat":       {"surface": None, "alpha": 0},
            "cold":       {"particles": [], "image": None},
            "clouds":     {"particles": [], "image": None},
        }
        self.load_images()

    def load_images(self):
        """
        Carga y escala las imágenes de partículas y capas de clima.

        Si alguna imagen no se puede cargar, se imprime un mensaje en consola
        y se usa un fallback dibujado con primitivas de pygame (líneas, círculos, etc.).
        """
        base_path = IMAGES_DIR  # antes: "images"

        # Tamaños relativos a TILE_SIZE
        rain_size  = (max(1, self.tile_size // 5), max(2, self.tile_size // 3))
        storm_size = (max(1, self.tile_size // 3), max(2, self.tile_size // 2))
        wind_size  = (max(1, self.tile_size // 3), max(1, self.tile_size // 6))
        cold_size  = (max(1, self.tile_size // 6), max(1, self.tile_size // 6))
        cloud_size = (self.tile_size * 3, int(self.tile_size * 1.5))

        def safe_load(name, size):
            """
            Intenta cargar una imagen desde disco y escalarla al tamaño dado.

            Si falla (archivo no encontrado o error de pygame), devuelve None
            y deja que el código use un fallback dibujado.
            """
            full_path = os.path.join(base_path, name)
            try:
                img = pygame.image.load(full_path).convert_alpha()
                return pygame.transform.scale(img, size)
            except (pygame.error, FileNotFoundError) as e:
                print(f"[WeatherVisuals] No se pudo cargar {name} desde {full_path}: {e}. Se usará fallback.")
                return None

        # Cargar imágenes (si faltan, se usan fallbacks dibujados)
        self.effects["rain"]["image"]    = safe_load("rain_drop.png",      rain_size)
        self.effects["storm"]["image"]   = safe_load("storm_drop.png",     storm_size)
        self.effects["wind"]["image"]    = safe_load("wind_particle.png",  wind_size)
        self.effects["cold"]["image"]    = safe_load("snowflake.png",      cold_size)
        self.effects["clouds"]["image"]  = safe_load("cloud_particle.png", cloud_size)

        # Capas para niebla y calor
        self.effects["fog"]["surface"]  = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        self.effects["heat"]["surface"] = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)

    def _create_particles(self, effect_name, num_particles, speed_min, speed_max, direction="down"):
        """
        Crea el conjunto inicial de partículas para un efecto climático.

        Parameters
        ----------
        effect_name : str
            Clave del efecto dentro de `self.effects` (por ejemplo, 'rain', 'clouds').
        num_particles : int
            Número de partículas a generar para el efecto.
        speed_min : float
            Velocidad mínima de movimiento de cada particula.
        speed_max : float
            Velocidad máxima de movimiento de cada particula.
        direction : {"down", "right"}
            Dirección dominante del movimiento. 'down' para lluvia/nieve,
            'right' para viento o nubes.
        """
        self.effects[effect_name]["particles"] = []
        for _ in range(num_particles):
            if direction == "down":
                x = random.randint(0, self.screen_width)
                y = random.randint(-self.screen_height, self.screen_height)
            else:  # "right"
                x = random.randint(-self.screen_width, 0)
                y = random.randint(0, self.screen_height)

            speed = random.uniform(speed_min, speed_max)
            size = random.randint(1, 3)
            self.effects[effect_name]["particles"].append([x, y, speed, size])

    def update(self, delta_time, current_condition, intensity=1.0):
        """
        Actualiza el estado interno de los efectos climáticos.

        Parameters
        ----------
        delta_time : float
            Tiempo transcurrido desde el último frame (en segundos). Se utiliza
            para actualizar posiciones de partículas de forma suave.
        current_condition : str
            Condición de clima actual (por ejemplo, 'rain', 'rain_light',
            'storm', 'fog', 'wind', 'cold', 'clouds', 'heat').
        intensity : float, opcional
            Factor de intensidad entre 0.0 y 1.0 que ajusta la cantidad de
            partículas y la opacidad de las capas (niebla/calor). Si no se
            especifica, se usa 1.0 para mantener compatibilidad con llamadas
            existentes.
        """
        self.current_condition = current_condition
        self.intensity = max(0.0, min(1.0, intensity))

        # --- Lluvia / tormenta ---
        if "rain" in self.current_condition or "storm" in self.current_condition:
            if not self.effects[self.current_condition]["particles"]:
                # Escala de partículas por intensidad (mín 50%, máx 150% del preset)
                scale = 0.5 + self.intensity
                if self.current_condition == "rain_light":
                    base_num, base_speed = 800, 200
                elif self.current_condition == "rain":
                    base_num, base_speed = 1500, 400
                else:  # storm
                    base_num, base_speed = 3000, 600

                num_particles = int(base_num * scale)
                speed = base_speed
                self._create_particles(
                    self.current_condition,
                    num_particles,
                    speed * 0.8,
                    speed * 1.2,
                    "down"
                )

            for drop in self.effects[self.current_condition]["particles"]:
                drop[1] += drop[2] * delta_time
                if drop[1] > self.screen_height:
                    drop[1] = random.randint(-50, -10)
                    drop[0] = random.randint(0, self.screen_width)
        else:
            for k in ["rain", "rain_light", "storm"]:
                self.effects[k]["particles"] = []

        # --- Nubes ---
        if self.current_condition == "clouds":
            if not self.effects["clouds"]["particles"]:
                num = max(3, int(5 * (0.5 + self.intensity)))  # 3–7 nubes
                self._create_particles("clouds", num, 20, 50, "right")
            for cloud in self.effects["clouds"]["particles"]:
                cloud[0] += cloud[2] * delta_time
                if cloud[0] > self.screen_width:
                    cloud[0] = -200
                    cloud[1] = random.randint(0, self.screen_height // 3)
        else:
            self.effects["clouds"]["particles"] = []

        # --- Viento ---
        if self.current_condition == "wind":
            if not self.effects["wind"]["particles"]:
                num = int(100 * (0.5 + self.intensity))
                self._create_particles("wind", max(50, num), 10, 20, "right")
            for p in self.effects["wind"]["particles"]:
                p[0] += p[2] * 10 * delta_time
                if p[0] > self.screen_width + 10:
                    p[0] = -10
                    p[1] = random.randint(0, self.screen_height)
        else:
            self.effects["wind"]["particles"] = []

        # --- Frío (nieve) ---
        if self.current_condition == "cold":
            if not self.effects["cold"]["particles"]:
                num = int(300 * (0.5 + self.intensity))
                self._create_particles("cold", max(150, num), 50, 100, "down")
            for p in self.effects["cold"]["particles"]:
                p[1] += p[2] * 0.5 * delta_time
                if p[1] > self.screen_height:
                    p[1] = random.randint(-50, -10)
                    p[0] = random.randint(0, self.screen_width)
        else:
            self.effects["cold"]["particles"] = []

        # --- Niebla ---
        target_fog_alpha = int(200 * self.intensity) if self.current_condition == "fog" else 0
        alpha = self.effects["fog"]["alpha"]
        if target_fog_alpha > alpha:
            self.effects["fog"]["alpha"] = min(target_fog_alpha, alpha + int(120 * delta_time))
        else:
            self.effects["fog"]["alpha"] = max(target_fog_alpha, alpha - int(120 * delta_time))

        # --- Calor ---
        target_heat_alpha = int(150 * self.intensity) if self.current_condition == "heat" else 0
        alpha = self.effects["heat"]["alpha"]
        if target_heat_alpha > alpha:
            self.effects["heat"]["alpha"] = min(target_heat_alpha, alpha + int(120 * delta_time))
        else:
            self.effects["heat"]["alpha"] = max(target_heat_alpha, alpha - int(120 * delta_time))

    def draw(self, screen):
        """
        Dibuja todos los efectos climáticos activos sobre la superficie dada.

        Parameters
        ----------
        screen : pygame.Surface
            Superficie principal de la ventana de juego donde se blitean las
            partículas (lluvia, nieve, nubes, viento) y las capas de niebla
            y calor semitransparentes.
        """
        # Lluvia / tormenta
        if "rain" in self.current_condition or "storm" in self.current_condition:
            key_for_image = "rain" if self.current_condition == "rain_light" else self.current_condition
            image = self.effects[key_for_image]["image"]
            for drop in self.effects[self.current_condition]["particles"]:
                if image:
                    screen.blit(image, (drop[0], drop[1]))
                else:
                    pygame.draw.line(
                        screen,
                        (100, 150, 255),
                        (drop[0], drop[1]),
                        (drop[0], drop[1] + 10),
                        1,
                    )

        # Viento
        if self.current_condition == "wind":
            image = self.effects["wind"]["image"]
            for p in self.effects["wind"]["particles"]:
                if image:
                    screen.blit(image, (p[0], p[1]))
                else:
                    pygame.draw.circle(
                        screen,
                        (255, 255, 255, 100),
                        (int(p[0]), int(p[1])),
                        p[2],
                    )

        # Frío (nieve)
        if self.current_condition == "cold":
            image = self.effects["cold"]["image"]
            for p in self.effects["cold"]["particles"]:
                if image:
                    screen.blit(image, (p[0], p[1]))
                else:
                    pygame.draw.circle(
                        screen,
                        (200, 200, 255),
                        (int(p[0]), int(p[1])),
                        p[2],
                    )

        # Nubes
        if self.current_condition == "clouds":
            image = self.effects["clouds"]["image"]
            for cloud in self.effects["clouds"]["particles"]:
                if image:
                    screen.blit(image, (cloud[0], cloud[1]))
                else:
                    pygame.draw.rect(
                        screen,
                        (255, 255, 255),
                        (cloud[0], cloud[1], 100, 50),
                    )

        # Capas de niebla/calor
        if self.effects["fog"]["alpha"] > 0:
            self.effects["fog"]["surface"].fill((128, 128, 128, self.effects["fog"]["alpha"]))
            screen.blit(self.effects["fog"]["surface"], (0, 0))

        if self.effects["heat"]["alpha"] > 0:
            self.effects["heat"]["surface"].fill((255, 100, 0, self.effects["heat"]["alpha"]))
            screen.blit(self.effects["heat"]["surface"], (0, 0))
