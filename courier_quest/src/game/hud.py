import pygame
import os

class HUD:
    """
    Gestiona y dibuja el Head-Up Display (Panel de Información) del juego.
    """
    def __init__(self, rect_area, screen_height, tile_size):
        """
        Inicializa el HUD.
        :param rect_area: Un objeto pygame.Rect que define la posición y el tamaño del panel.
        :param screen_height: La altura de la pantalla del mapa del juego (para referencia).
        :param tile_size: El tamaño de los tiles (para referencia).
        """
        self.rect = rect_area
        self.screen_height = screen_height # Almacenado
        self.tile_size = tile_size         # Almacenado
        
        self.background_color = (20, 20, 20)  # Color de fondo oscuro para el panel
        self.text_color = (255, 255, 255)     # Color del texto (blanco)
        
        # Carga de fuentes
        self.font = self.load_font(20)
        self.title_font = self.load_font(28)
        
    def load_font(self, size):
        """Intenta cargar una fuente o usa la predeterminada de Pygame."""
        try:
            # Reemplaza 'RussoOne-Regular.ttf' con tu fuente si tienes una
            font_path = os.path.join('fonts', 'RussoOne-Regular.ttf')
            return pygame.font.Font(font_path, size)
        except:
            return pygame.font.Font(None, size)

    def draw_text(self, surface, text, font, color, x, y, align='left'):
        """Función auxiliar para dibujar texto."""
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        
        if align == 'left':
            text_rect.topleft = (x, y)
        elif align == 'center':
            text_rect.midtop = (x, y)
        elif align == 'right':
            text_rect.topright = (x, y)
            
        surface.blit(text_surface, text_rect)

    def draw(self, screen, courier, weather_condition, speed_multiplier, remaining_time=0, goal_income=0):
       
        """
        Dibuja el panel de información completo.
        :param screen: La superficie de Pygame donde dibujar.
        :param courier: Instancia de la clase Courier.
        :param weather_condition: Nombre de la condición climática actual (string).
        :param speed_multiplier: Multiplicador de velocidad actual del clima.
        :param remaining_time: Tiempo restante en segundos.
        :param goal_income: Ingreso objetivo para el nivel.
        """
        # --- Dibujar el fondo del panel ---
        pygame.draw.rect(screen, self.background_color, self.rect)
        
        # Coordenadas de inicio para el contenido
        padding = 20
        start_x = self.rect.left + padding
        start_y = self.rect.top + padding
        line_spacing = 30

        # --- Título ---
        self.draw_text(screen, "COURIER QUEST", self.title_font, (255, 215, 0), 
                       self.rect.centerx, start_y, align='center')
        start_y += 60 # Espacio después del título

        # --- Tiempo e ingresos ---
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        self.draw_text(screen, f"Tiempo: {minutes:02d}:{seconds:02d}", self.font, self.text_color, start_x, start_y)
        start_y += line_spacing
        
        self.draw_text(screen, f"Ingresos: {courier.income}/{int(goal_income)}", 
                       self.font, self.text_color, start_x, start_y)
        start_y += line_spacing

        # --- Courier --- (info del repartidor)
        self.draw_text(screen, "--- Repartidor ---", self.font, self.text_color, start_x, start_y)
        start_y += line_spacing
        
        self.draw_text(screen, f"Posición: ({courier.x}, {courier.y})", self.font, self.text_color, start_x, start_y)
        start_y += line_spacing
        
        self.draw_text(screen, f"Pedidos: {courier.packages_delivered}", self.font, self.text_color, start_x, start_y)
        start_y += line_spacing
        
        # --- Barra de resistencia --- (Stamina)
        stamina_percent = courier.stamina / courier.max_stamina
        stamina_bar_rect = pygame.Rect(start_x, start_y, self.rect.width - 2 * padding, 20)
        
        # Fondo gris de la barra
        pygame.draw.rect(screen, (50, 50, 50), stamina_bar_rect)
        # Nivel de resistencia
        fill_width = stamina_bar_rect.width * stamina_percent
        fill_rect = pygame.Rect(start_x, start_y, fill_width, 20)
        
        # Color: Rojo si es bajo, Verde si es alto
        stamina_color = (255, 50, 50) if stamina_percent < 0.3 else (50, 255, 50)
        pygame.draw.rect(screen, stamina_color, fill_rect)
        
        # Texto sobre la barra
        stamina_text = f"Resistencia: {int(courier.stamina)}/{int(courier.max_stamina)}"
        self.draw_text(screen, stamina_text, self.font, self.text_color, start_x + stamina_bar_rect.width / 2, start_y + 2, align='center')
        
        start_y += line_spacing + 10 # Espacio después de la barra
        
        # --- Reputación ---
        self.draw_text(screen, f"Reputación: {courier.reputation}", self.font, self.text_color, start_x, start_y)
        start_y += line_spacing

        # --- Clima ---
        self.draw_text(screen, "--- Clima ---", self.font, self.text_color, start_x, start_y)
        start_y += line_spacing
        
        # Capitaliza la primera letra del clima
        weather_display = weather_condition.replace('_', ' ').title()
        self.draw_text(screen, f"Condición: {weather_display}", self.font, self.text_color, start_x, start_y)
        start_y += line_spacing
        
        # Muestra el impacto en la velocidad
        speed_impact = f"{int(speed_multiplier * 100)}%"
        self.draw_text(screen, f"Vel. (Mult.): {speed_impact}", self.font, self.text_color, start_x, start_y)

""" 
Ahora muestra:
Tiempo restante (mm:ss)
Ingresos actuales y meta (courier.income/goal_income)
Reputación (según reglas del juego)

Entonces ya nuestro hud cumple con lo de las condiciones de victoria/derrota
"""