import pygame
import os

class HUD:
    def __init__(self, rect_area, screen_height, tile_size):
        self.rect = rect_area
        self.screen_height = screen_height
        self.tile_size = tile_size
        
        self.background_color = (20, 20, 20)
        self.text_color = (255, 255, 255)
        self.highlight_color = (255, 215, 0)
        self.warning_color = (255, 100, 100)
        self.success_color = (100, 255, 100)
        
        # Carga de fuentes
        self.font = self.load_font(20)
        self.title_font = self.load_font(28)
        self.small_font = self.load_font(16)
        
    def load_font(self, size):
        try:
            font_path = os.path.join('fonts', 'RussoOne-Regular.ttf')
            return pygame.font.Font(font_path, size)
        except:
            return pygame.font.Font(None, size)

    def draw_text(self, surface, text, font, color, x, y, align='left'):
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
        # --- Dibujar el fondo del panel ---
        pygame.draw.rect(screen, self.background_color, self.rect)
        
        # Coordenadas de inicio
        padding = 20
        start_x = self.rect.left + padding
        start_y = self.rect.top + padding
        line_spacing = 30
        small_spacing = 22

        # --- TÍTULO ---
        self.draw_text(screen, "COURIER QUEST", self.title_font, self.highlight_color, 
                       self.rect.centerx, start_y, align='center')
        start_y += 50

        # --- TIEMPO E INGRESOS ---
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        time_color = self.warning_color if remaining_time < 60 else self.text_color
        self.draw_text(screen, f"Tiempo: {minutes:02d}:{seconds:02d}", self.font, time_color, start_x, start_y)
        start_y += line_spacing
        
        income_color = self.success_color if courier.income >= goal_income else self.text_color
        self.draw_text(screen, f"Ingresos: ${courier.income}/{int(goal_income)}", 
                       self.font, income_color, start_x, start_y)
        start_y += line_spacing

        # --- REPARTIDOR ---
        self.draw_text(screen, "--- Repartidor ---", self.small_font, self.text_color, start_x, start_y)
        start_y += small_spacing
        self.draw_text(screen, f"Posición: ({courier.x}, {courier.y})", self.small_font, self.text_color, start_x, start_y)
        start_y += small_spacing
        self.draw_text(screen, f"Entregados: {courier.packages_delivered}", self.small_font, self.text_color, start_x, start_y)
        start_y += small_spacing
        
        # --- BARRA DE RESISTENCIA ---
        stamina_percent = courier.stamina / courier.max_stamina
        stamina_bar_rect = pygame.Rect(start_x, start_y, self.rect.width - 2 * padding, 20)
        pygame.draw.rect(screen, (50, 50, 50), stamina_bar_rect)
        fill_width = stamina_bar_rect.width * stamina_percent
        fill_rect = pygame.Rect(start_x, start_y, fill_width, 20)
        stamina_color = self.warning_color if stamina_percent < 0.3 else self.success_color
        pygame.draw.rect(screen, stamina_color, fill_rect)
        stamina_text = f"Resistencia: {int(courier.stamina)}/{int(courier.max_stamina)}"
        self.draw_text(screen, stamina_text, self.small_font, self.text_color, 
                      start_x + stamina_bar_rect.width / 2, start_y + 2, align='center')
        start_y += line_spacing + 10
        
        # --- REPUTACIÓN ---
        rep_color = self.success_color if courier.reputation >= 90 else self.warning_color if courier.reputation < 30 else self.text_color
        self.draw_text(screen, f"Reputación: {courier.reputation}", self.font, rep_color, start_x, start_y)
        start_y += line_spacing

        # --- INVENTARIO ---
        self.draw_text(screen, "--- Inventario ---", self.small_font, self.text_color, start_x, start_y)
        start_y += small_spacing
        
        if courier.has_jobs():
            current_job = courier.get_current_job()
            self.draw_text(screen, f"Pedido: {current_job.id}", self.small_font, self.highlight_color, start_x, start_y)
            start_y += small_spacing
            self.draw_text(screen, f"Pago: ${current_job.payout}", self.small_font, self.text_color, start_x, start_y)
            start_y += small_spacing
            self.draw_text(screen, f"Peso: {courier.current_weight}/{courier.max_weight}kg", self.small_font, self.text_color, start_x, start_y)
            start_y += small_spacing
        else:
            self.draw_text(screen, "Sin pedidos", self.small_font, (150, 150, 150), start_x, start_y)
            start_y += small_spacing
        
        start_y += line_spacing - small_spacing

        # --- CLIMA ---
        self.draw_text(screen, "--- Clima ---", self.small_font, self.text_color, start_x, start_y)
        start_y += small_spacing
        weather_display = weather_condition.replace('_', ' ').title()
        self.draw_text(screen, f"Condición: {weather_display}", self.small_font, self.text_color, start_x, start_y)
        start_y += small_spacing
        speed_impact = f"{int(speed_multiplier * 100)}%"
        self.draw_text(screen, f"Velocidad: {speed_impact}", self.small_font, self.text_color, start_x, start_y)
        start_y += small_spacing

        # --- CONTROLES BÁSICOS ---
        start_y += 10
        self.draw_text(screen, "--- Controles ---", self.small_font, (200, 200, 255), start_x, start_y)
        start_y += small_spacing
        
        basic_controls = [
            "Flechas: Moverse",
            "ESPACIO: Recoger",
            "E: Entregar",
            "TAB: Cambiar pedido",
            "A: Ver pedidos cerca"
        ]
        
        for control in basic_controls:
            self.draw_text(screen, control, self.small_font, (180, 180, 180), start_x, start_y)
            start_y += small_spacing - 5

        # --- CONTROLES DE ORDENAMIENTO (NUEVO) ---
        start_y += 5
        self.draw_text(screen, "--- Ordenar ---", self.small_font, (200, 255, 200), start_x, start_y)
        start_y += small_spacing
        
        sort_controls = [
            "F1: Por Prioridad",
            "F2: Por Tiempo", 
            "F3: Por Pago",
            "F4: Orden original"
        ]
        
        for control in sort_controls:
            self.draw_text(screen, control, self.small_font, (180, 230, 180), start_x, start_y)
            start_y += small_spacing - 5

        # --- CONTROLES DEL SISTEMA ---
        start_y += 5
        self.draw_text(screen, "--- Sistema ---", self.small_font, (200, 200, 255), start_x, start_y)
        start_y += small_spacing
        
        system_controls = [
            "Ctrl+S: Guardar",
            "Ctrl+L: Cargar"
        ]
        
        for control in system_controls:
            self.draw_text(screen, control, self.small_font, (180, 180, 180), start_x, start_y)
            start_y += small_spacing - 5