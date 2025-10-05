""""
import pygame
import os
import random

class WeatherVisuals:
    def __init__(self, screen_size, tile_size):
        self.screen_width, self.screen_height = screen_size
        self.tile_size = tile_size  # Guardamos el TILE_SIZE
        self.effects = {
            "rain": {"particles": [], "image": None},
            "rain_light": {"particles": [], "image": None},
            "storm": {"particles": [], "image": None},
            "fog": {"surface": None, "alpha": 0},
            "wind": {"particles": [], "image": None},
            "heat": {"surface": None, "alpha": 0},
            "cold": {"particles": [], "image": None},
            "clouds": {"particles": [], "image": None},
        }
        self.load_images()
        self.current_condition = "clear"

    def load_images(self):
        base_path = "images"
        
        # Dimensiones para las partículas, escaladas con TILE_SIZE
        rain_size = (self.tile_size // 5, self.tile_size // 3)
        storm_size = (self.tile_size // 3, self.tile_size // 2)
        wind_size = (self.tile_size // 3, self.tile_size // 6)
        cold_size = (self.tile_size // 6, self.tile_size // 6)
        cloud_size = (self.tile_size * 3, self.tile_size * 1.5)

        try:
            image = pygame.image.load(os.path.join(base_path, "rain_drop.png")).convert_alpha()
            self.effects["rain"]["image"] = pygame.transform.scale(image, rain_size)
        except pygame.error as e:
            print(f"Error al cargar imagen de lluvia: {e}. Usando dibujo simple.")
            self.effects["rain"]["image"] = None
        
        try:
            image = pygame.image.load(os.path.join(base_path, "storm_drop.png")).convert_alpha()
            self.effects["storm"]["image"] = pygame.transform.scale(image, storm_size)
        except pygame.error as e:
            print(f"Error al cargar imagen de tormenta: {e}. Usando dibujo simple.")
            self.effects["storm"]["image"] = None
        
        try:
            image = pygame.image.load(os.path.join(base_path, "wind_particle.png")).convert_alpha()
            self.effects["wind"]["image"] = pygame.transform.scale(image, wind_size)
        except pygame.error as e:
            print(f"Error al cargar imagen de viento: {e}. Usando dibujo simple.")
            self.effects["wind"]["image"] = None

        try:
            image = pygame.image.load(os.path.join(base_path, "snowflake.png")).convert_alpha()
            self.effects["cold"]["image"] = pygame.transform.scale(image, cold_size)
        except pygame.error as e:
            print(f"Error al cargar imagen de frío: {e}. Usando dibujo simple.")
            self.effects["cold"]["image"] = None

        try:
            image = pygame.image.load(os.path.join(base_path, "cloud_particle.png")).convert_alpha()
            self.effects["clouds"]["image"] = pygame.transform.scale(image, cloud_size)
        except pygame.error as e:
            print(f"Error al cargar imagen de nubes: {e}. Usando dibujo simple.")
            self.effects["clouds"]["image"] = None

        self.effects["fog"]["surface"] = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        self.effects["heat"]["surface"] = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
    
    def _create_particles(self, effect_name, num_particles, speed_min, speed_max, direction="down"):
        self.effects[effect_name]["particles"] = []
        for _ in range(num_particles):
            if direction == "down":
                x = random.randint(0, self.screen_width)
                y = random.randint(-self.screen_height, self.screen_height)
            elif direction == "right":
                x = random.randint(-self.screen_width, 0)
                y = random.randint(0, self.screen_height)
            
            speed = random.uniform(speed_min, speed_max)
            size = random.randint(1, 3)
            self.effects[effect_name]["particles"].append([x, y, speed, size])

    def update(self, delta_time, current_condition):
        self.current_condition = current_condition

        if "rain" in self.current_condition or "storm" in self.current_condition:
            if not self.effects[self.current_condition]["particles"]:
                if self.current_condition == "rain_light":
                    num_particles = 800
                    speed = 200
                elif self.current_condition == "rain":
                    num_particles = 1500
                    speed = 400
                elif self.current_condition == "storm":
                    num_particles = 3000
                    speed = 600
                self._create_particles(self.current_condition, num_particles, speed * 0.8, speed * 1.2, "down")

            for drop in self.effects[self.current_condition]["particles"]:
                drop[1] += drop[2] * delta_time
                if drop[1] > self.screen_height:
                    drop[1] = random.randint(-50, -10)
                    drop[0] = random.randint(0, self.screen_width)
        else:
            for key in ["rain", "rain_light", "storm"]:
                self.effects[key]["particles"] = []
        
        if self.current_condition == "clouds":
            if not self.effects["clouds"]["particles"]:
                self._create_particles("clouds", 5, 20, 50, "right")
            for cloud in self.effects["clouds"]["particles"]:
                cloud[0] += cloud[2] * delta_time
                if cloud[0] > self.screen_width:
                    cloud[0] = -200
                    cloud[1] = random.randint(0, self.screen_height // 3)
        else:
            self.effects["clouds"]["particles"] = []

        if self.current_condition == "wind":
            if not self.effects["wind"]["particles"]:
                self._create_particles("wind", 100, 10, 20, "right")
            for particle in self.effects["wind"]["particles"]:
                particle[0] += particle[2] * 10 * delta_time
                if particle[0] > self.screen_width + 10:
                    particle[0] = -10
                    particle[1] = random.randint(0, self.screen_height)
        else:
            self.effects["wind"]["particles"] = []

        if self.current_condition == "cold":
            if not self.effects["cold"]["particles"]:
                self._create_particles("cold", 300, 50, 100, "down")
            for particle in self.effects["cold"]["particles"]:
                particle[1] += particle[2] * 0.5 * delta_time
                if particle[1] > self.screen_height:
                    particle[1] = random.randint(-50, -10)
                    particle[0] = random.randint(0, self.screen_width)
        else:
            self.effects["cold"]["particles"] = []

        if self.current_condition == "fog":
            self.effects["fog"]["alpha"] = min(200, self.effects["fog"]["alpha"] + 100 * delta_time)
        else:
            self.effects["fog"]["alpha"] = max(0, self.effects["fog"]["alpha"] - 100 * delta_time)

        if self.current_condition == "heat":
            self.effects["heat"]["alpha"] = min(150, self.effects["heat"]["alpha"] + 100 * delta_time)
        else:
            self.effects["heat"]["alpha"] = max(0, self.effects["heat"]["alpha"] - 100 * delta_time)

    def draw(self, screen):
        if "rain" in self.current_condition or "storm" in self.current_condition:
            image = self.effects["rain"]["image"] if self.current_condition == "rain_light" else self.effects[self.current_condition]["image"]
            for drop in self.effects[self.current_condition]["particles"]:
                if image:
                    screen.blit(image, (drop[0], drop[1]))
                else:
                    pygame.draw.line(screen, (100, 150, 255), (drop[0], drop[1]), (drop[0], drop[1] + 10), 1)

        if self.current_condition == "wind":
            image = self.effects["wind"]["image"]
            for particle in self.effects["wind"]["particles"]:
                if image:
                    screen.blit(image, (particle[0], particle[1]))
                else:
                    pygame.draw.circle(screen, (255, 255, 255, 100), (int(particle[0]), int(particle[1])), particle[2])

        if self.current_condition == "cold":
            image = self.effects["cold"]["image"]
            for particle in self.effects["cold"]["particles"]:
                if image:
                    screen.blit(image, (particle[0], particle[1]))
                else:
                    pygame.draw.circle(screen, (200, 200, 255), (int(particle[0]), int(particle[1])), particle[2])

        if self.current_condition == "clouds":
            image = self.effects["clouds"]["image"]
            for cloud in self.effects["clouds"]["particles"]:
                if image:
                    screen.blit(image, (cloud[0], cloud[1]))
                else:
                    pygame.draw.rect(screen, (255, 255, 255), (cloud[0], cloud[1], 100, 50))

        if self.effects["fog"]["alpha"] > 0:
            self.effects["fog"]["surface"].fill((128, 128, 128, self.effects["fog"]["alpha"]))
            screen.blit(self.effects["fog"]["surface"], (0, 0))

        if self.effects["heat"]["alpha"] > 0:
            self.effects["heat"]["surface"].fill((255, 100, 0, self.effects["heat"]["alpha"]))
            screen.blit(self.effects["heat"]["surface"], (0, 0))

"""

import pygame
import os
import random

class WeatherVisuals:
    """
    Efectos visuales de clima. Usa 'intensity' (0–1) para escalar cantidad de particulas
    y opacidad de capas (niebla/calor). Si no se pasa la intensidad, usa 1.0 por compatibilidad.
    """
    def __init__(self, screen_size, tile_size):
        self.screen_width, self.screen_height = screen_size
        self.tile_size = tile_size
        self.current_condition = "clear"
        self.intensity = 1.0  # por defecto

        # Partículas/superficies por condición
        self.effects = {
            "rain":   {"particles": [], "image": None},
            "rain_light": {"particles": [], "image": None},
            "storm":  {"particles": [], "image": None},
            "fog":    {"surface": None, "alpha": 0},
            "wind":   {"particles": [], "image": None},
            "heat":   {"surface": None, "alpha": 0},
            "cold":   {"particles": [], "image": None},
            "clouds": {"particles": [], "image": None},
        }
        self.load_images()

    def load_images(self):
        base_path = "images"

        # Tamaños relativos a TILE_SIZE
        rain_size  = (max(1, self.tile_size // 5), max(2, self.tile_size // 3))
        storm_size = (max(1, self.tile_size // 3), max(2, self.tile_size // 2))
        wind_size  = (max(1, self.tile_size // 3), max(1, self.tile_size // 6))
        cold_size  = (max(1, self.tile_size // 6), max(1, self.tile_size // 6))
        cloud_size = (self.tile_size * 3, int(self.tile_size * 1.5))

        def safe_load(name, size):
            try:
                img = pygame.image.load(os.path.join(base_path, name)).convert_alpha()
                return pygame.transform.scale(img, size)
            except pygame.error as e:
                print(f"[WeatherVisuals] No se pudo cargar {name}: {e}. Se usará fallback.")
                return None

        self.effects["rain"]["image"]  = safe_load("rain_drop.png",  rain_size)
        self.effects["storm"]["image"] = safe_load("storm_drop.png", storm_size)
        self.effects["wind"]["image"]  = safe_load("wind_particle.png", wind_size)
        self.effects["cold"]["image"]  = safe_load("snowflake.png", cold_size)
        self.effects["clouds"]["image"]= safe_load("cloud_particle.png", cloud_size)

        self.effects["fog"]["surface"]  = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        self.effects["heat"]["surface"] = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)

    def _create_particles(self, effect_name, num_particles, speed_min, speed_max, direction="down"):
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
        Actualiza partículas según condición actual. 'intensity' escala cantidad/opacidad.
        Mantiene compatibilidad con llamadas antiguas (intensity por defecto=1.0).
        """
        self.current_condition = current_condition
        self.intensity = max(0.0, min(1.0, intensity))

        # --- Lluvia/tormenta ---
        if "rain" in self.current_condition or "storm" in self.current_condition:
            if not self.effects[self.current_condition]["particles"]:
                # Escala de partículas por intensidad (mín 50% máx 150% del preset)
                scale = 0.5 + self.intensity
                if self.current_condition == "rain_light":
                    base_num, base_speed = 800, 200
                elif self.current_condition == "rain":
                    base_num, base_speed = 1500, 400
                else:  # storm
                    base_num, base_speed = 3000, 600

                num_particles = int(base_num * scale)
                speed = base_speed
                self._create_particles(self.current_condition, num_particles, speed * 0.8, speed * 1.2, "down")

            for drop in self.effects[self.current_condition]["particles"]:
                drop[1] += drop[2] * delta_time
                if drop[1] > self.screen_height:
                    drop[1] = random.randint(-50, -10)
                    drop[0] = random.randint(0, self.screen_width)
        else:
            for k in ["rain", "rain_light", "storm"]:
                self.effects[k]["particles"] = []

        # --- Nubes desplazándose ---
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

        # --- Frio (nieve) ---
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
        # Lluvia/tormenta
        if "rain" in self.current_condition or "storm" in self.current_condition:
            key = "rain" if self.current_condition == "rain_light" else self.current_condition
            image = self.effects[key]["image"]
            for drop in self.effects[self.current_condition]["particles"]:
                if image:
                    screen.blit(image, (drop[0], drop[1]))
                else:
                    pygame.draw.line(screen, (100, 150, 255), (drop[0], drop[1]), (drop[0], drop[1] + 10), 1)

        # Viento
        if self.current_condition == "wind":
            image = self.effects["wind"]["image"]
            for p in self.effects["wind"]["particles"]:
                if image:
                    screen.blit(image, (p[0], p[1]))
                else:
                    pygame.draw.circle(screen, (255, 255, 255, 100), (int(p[0]), int(p[1])), p[2])

        # Frio (nieve)
        if self.current_condition == "cold":
            image = self.effects["cold"]["image"]
            for p in self.effects["cold"]["particles"]:
                if image:
                    screen.blit(image, (p[0], p[1]))
                else:
                    pygame.draw.circle(screen, (200, 200, 255), (int(p[0]), int(p[1])), p[2])

        # Nubes
        if self.current_condition == "clouds":
            image = self.effects["clouds"]["image"]
            for cloud in self.effects["clouds"]["particles"]:
                if image:
                    screen.blit(image, (cloud[0], cloud[1]))
                else:
                    pygame.draw.rect(screen, (255, 255, 255), (cloud[0], cloud[1], 100, 50))

        # Capas de niebla/calor
        if self.effects["fog"]["alpha"] > 0:
            self.effects["fog"]["surface"].fill((128, 128, 128, self.effects["fog"]["alpha"]))
            screen.blit(self.effects["fog"]["surface"], (0, 0))

        if self.effects["heat"]["alpha"] > 0:
            self.effects["heat"]["surface"].fill((255, 100, 0, self.effects["heat"]["alpha"]))
            screen.blit(self.effects["heat"]["surface"], (0, 0))

"""
Esta versión incluye:
- Escalado por intensidad: mas particulas/niebla/calor segun rafaga
- Tamaños de particulas relativos a TILE_SIZE
"""