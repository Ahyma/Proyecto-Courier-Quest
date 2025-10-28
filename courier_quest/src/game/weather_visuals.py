import pygame
import os
import random

class WeatherVisuals:
    """
    Sistema de efectos visuales para diferentes condiciones climáticas.
    
    Características:
    - Partículas para lluvia, nieve, viento, etc.
    - Capas de niebla y calor con alpha
    - Escalado por intensidad del clima
    - Tamaños relativos a TILE_SIZE
    """
    
    def __init__(self, screen_size, tile_size):
        """
        Inicializa el sistema de efectos visuales climáticos.
        
        Args:
            screen_size: Tamaño de la pantalla (ancho, alto)
            tile_size: Tamaño de los tiles para escalado
        """
        self.screen_width, self.screen_height = screen_size
        self.tile_size = tile_size
        self.current_condition = "clear"
        self.intensity = 1.0  # Intensidad por defecto (0-1)

        # Diccionario de efectos por condición climática
        self.effects = {
            "rain":   {"particles": [], "image": None},      # Lluvia normal
            "rain_light": {"particles": [], "image": None},  # Lluvia ligera
            "storm":  {"particles": [], "image": None},      # Tormenta
            "fog":    {"surface": None, "alpha": 0},         # Niebla (capa semitransparente)
            "wind":   {"particles": [], "image": None},      # Viento
            "heat":   {"surface": None, "alpha": 0},         # Calor (capa naranja)
            "cold":   {"particles": [], "image": None},      # Frío (nieve)
            "clouds": {"particles": [], "image": None},      # Nubes
        }
        self.load_images()

    def load_images(self):
        """Carga y escala las imágenes para las partículas climáticas."""
        base_path = "images"

        # Tamaños relativos a TILE_SIZE para escalado consistente
        rain_size  = (max(1, self.tile_size // 5), max(2, self.tile_size // 3))
        storm_size = (max(1, self.tile_size // 3), max(2, self.tile_size // 2))
        wind_size  = (max(1, self.tile_size // 3), max(1, self.tile_size // 6))
        cold_size  = (max(1, self.tile_size // 6), max(1, self.tile_size // 6))
        cloud_size = (self.tile_size * 3, int(self.tile_size * 1.5))

        def safe_load(name, size):
            """Función auxiliar para cargar imágenes con manejo de errores."""
            try:
                img = pygame.image.load(os.path.join(base_path, name)).convert_alpha()
                return pygame.transform.scale(img, size)
            except pygame.error as e:
                print(f"[WeatherVisuals] No se pudo cargar {name}: {e}. Se usará fallback.")
                return None

        # Cargar todas las imágenes necesarias
        self.effects["rain"]["image"]  = safe_load("rain_drop.png",  rain_size)
        self.effects["storm"]["image"] = safe_load("storm_drop.png", storm_size)
        self.effects["wind"]["image"]  = safe_load("wind_particle.png", wind_size)
        self.effects["cold"]["image"]  = safe_load("snowflake.png", cold_size)
        self.effects["clouds"]["image"]= safe_load("cloud_particle.png", cloud_size)

        # Crear superficies para efectos de capa (niebla, calor)
        self.effects["fog"]["surface"]  = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        self.effects["heat"]["surface"] = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)

    def _create_particles(self, effect_name, num_particles, speed_min, speed_max, direction="down"):
        """
        Crea un conjunto de partículas para un efecto.
        
        Args:
            effect_name: Nombre del efecto en self.effects
            num_particles: Cantidad de partículas a crear
            speed_min: Velocidad mínima de partículas
            speed_max: Velocidad máxima de partículas
            direction: "down" (caída) o "right" (desplazamiento horizontal)
        """
        self.effects[effect_name]["particles"] = []
        for _ in range(num_particles):
            if direction == "down":
                # Partículas que caen desde arriba
                x = random.randint(0, self.screen_width)
                y = random.randint(-self.screen_height, self.screen_height)
            else:  # "right"
                # Partículas que se mueven horizontalmente desde la izquierda
                x = random.randint(-self.screen_width, 0)
                y = random.randint(0, self.screen_height)

            speed = random.uniform(speed_min, speed_max)
            size = random.randint(1, 3)
            self.effects[effect_name]["particles"].append([x, y, speed, size])

    def update(self, delta_time, current_condition, intensity=1.0):
        """
        Actualiza todas las partículas y efectos visuales.
        
        Args:
            delta_time: Tiempo transcurrido desde última actualización
            current_condition: Condición climática actual
            intensity: Intensidad del efecto (0-1)
        """
        self.current_condition = current_condition
        self.intensity = max(0.0, min(1.0, intensity))  # Asegurar rango 0-1

        # --- Lluvia/tormenta ---
        if "rain" in self.current_condition or "storm" in self.current_condition:
            if not self.effects[self.current_condition]["particles"]:
                # Escalar cantidad de partículas por intensidad
                scale = 0.5 + self.intensity  # 50% a 150% del preset base
                
                # Configuración base por tipo de lluvia
                if self.current_condition == "rain_light":
                    base_num, base_speed = 800, 200
                elif self.current_condition == "rain":
                    base_num, base_speed = 1500, 400
                else:  # storm
                    base_num, base_speed = 3000, 600

                num_particles = int(base_num * scale)
                speed = base_speed
                self._create_particles(self.current_condition, num_particles, speed * 0.8, speed * 1.2, "down")

            # Actualizar posición de cada gota
            for drop in self.effects[self.current_condition]["particles"]:
                drop[1] += drop[2] * delta_time  # Mover hacia abajo
                if drop[1] > self.screen_height:  # Reaparecer arriba si sale de pantalla
                    drop[1] = random.randint(-50, -10)
                    drop[0] = random.randint(0, self.screen_width)
        else:
            # Limpiar partículas de lluvia si no es necesario
            for k in ["rain", "rain_light", "storm"]:
                self.effects[k]["particles"] = []

        # --- Nubes desplazándose ---
        if self.current_condition == "clouds":
            if not self.effects["clouds"]["particles"]:
                num = max(3, int(5 * (0.5 + self.intensity)))  # 3–7 nubes según intensidad
                self._create_particles("clouds", num, 20, 50, "right")
            for cloud in self.effects["clouds"]["particles"]:
                cloud[0] += cloud[2] * delta_time  # Mover hacia la derecha
                if cloud[0] > self.screen_width:  # Reaparecer a la izquierda
                    cloud[0] = -200
                    cloud[1] = random.randint(0, self.screen_height // 3)
        else:
            self.effects["clouds"]["particles"] = []

        # --- Viento ---
        if self.current_condition == "wind":
            if not self.effects["wind"]["particles"]:
                num = int(100 * (0.5 + self.intensity))  # 50-150 partículas
                self._create_particles("wind", max(50, num), 10, 20, "right")
            for p in self.effects["wind"]["particles"]:
                p[0] += p[2] * 10 * delta_time  # Movimiento rápido horizontal
                if p[0] > self.screen_width + 10:  # Reaparecer a la izquierda
                    p[0] = -10
                    p[1] = random.randint(0, self.screen_height)
        else:
            self.effects["wind"]["particles"] = []

        # --- Frio (nieve) ---
        if self.current_condition == "cold":
            if not self.effects["cold"]["particles"]:
                num = int(300 * (0.5 + self.intensity))  # 150-450 copos de nieve
                self._create_particles("cold", max(150, num), 50, 100, "down")
            for p in self.effects["cold"]["particles"]:
                p[1] += p[2] * 0.5 * delta_time  # Caída lenta
                if p[1] > self.screen_height:  # Reaparecer arriba
                    p[1] = random.randint(-50, -10)
                    p[0] = random.randint(0, self.screen_width)
        else:
            self.effects["cold"]["particles"] = []

        # --- Niebla (transición suave de alpha) ---
        target_fog_alpha = int(200 * self.intensity) if self.current_condition == "fog" else 0
        alpha = self.effects["fog"]["alpha"]
        if target_fog_alpha > alpha:
            self.effects["fog"]["alpha"] = min(target_fog_alpha, alpha + int(120 * delta_time))
        else:
            self.effects["fog"]["alpha"] = max(target_fog_alpha, alpha - int(120 * delta_time))

        # --- Calor (transición suave de alpha) ---
        target_heat_alpha = int(150 * self.intensity) if self.current_condition == "heat" else 0
        alpha = self.effects["heat"]["alpha"]
        if target_heat_alpha > alpha:
            self.effects["heat"]["alpha"] = min(target_heat_alpha, alpha + int(120 * delta_time))
        else:
            self.effects["heat"]["alpha"] = max(target_heat_alpha, alpha - int(120 * delta_time))

    def draw(self, screen):
        """Dibuja todos los efectos visuales activos en la pantalla."""
        
        # Lluvia/tormenta
        if "rain" in self.current_condition or "storm" in self.current_condition:
            key = "rain" if self.current_condition == "rain_light" else self.current_condition
            image = self.effects[key]["image"]
            for drop in self.effects[self.current_condition]["particles"]:
                if image:
                    screen.blit(image, (drop[0], drop[1]))  # Usar imagen si está disponible
                else:
                    # Fallback: dibujar línea azul
                    pygame.draw.line(screen, (100, 150, 255), (drop[0], drop[1]), (drop[0], drop[1] + 10), 1)

        # Viento
        if self.current_condition == "wind":
            image = self.effects["wind"]["image"]
            for p in self.effects["wind"]["particles"]:
                if image:
                    screen.blit(image, (p[0], p[1]))
                else:
                    # Fallback: círculo blanco semitransparente
                    pygame.draw.circle(screen, (255, 255, 255, 100), (int(p[0]), int(p[1])), p[2])

        # Frio (nieve)
        if self.current_condition == "cold":
            image = self.effects["cold"]["image"]
            for p in self.effects["cold"]["particles"]:
                if image:
                    screen.blit(image, (p[0], p[1]))
                else:
                    # Fallback: círculo azul claro
                    pygame.draw.circle(screen, (200, 200, 255), (int(p[0]), int(p[1])), p[2])

        # Nubes
        if self.current_condition == "clouds":
            image = self.effects["clouds"]["image"]
            for cloud in self.effects["clouds"]["particles"]:
                if image:
                    screen.blit(image, (cloud[0], cloud[1]))
                else:
                    # Fallback: rectángulo blanco
                    pygame.draw.rect(screen, (255, 255, 255), (cloud[0], cloud[1], 100, 50))

        # Capas de niebla/calor (si tienen alpha > 0)
        if self.effects["fog"]["alpha"] > 0:
            self.effects["fog"]["surface"].fill((128, 128, 128, self.effects["fog"]["alpha"]))
            screen.blit(self.effects["fog"]["surface"], (0, 0))

        if self.effects["heat"]["alpha"] > 0:
            self.effects["heat"]["surface"].fill((255, 100, 0, self.effects["heat"]["alpha"]))
            screen.blit(self.effects["heat"]["surface"], (0, 0))