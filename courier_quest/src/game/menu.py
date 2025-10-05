import pygame
import os
from game.save_game import load_slot

class MainMenu:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.buttons = []
        self.selected_button = 0
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        
        # Colores
        self.bg_color = (20, 30, 40)
        self.title_color = (255, 215, 0)
        self.button_color = (70, 130, 180)
        self.button_hover_color = (100, 160, 210)
        self.button_text_color = (255, 255, 255)
        self.button_disabled_color = (100, 100, 100)
        
        self.load_fonts()
        self.create_buttons()
        
    def load_fonts(self):
        """Carga las fuentes para el menú"""
        try:
            font_path = os.path.join("fonts", "RussoOne-Regular.ttf")
            self.font_large = pygame.font.Font(font_path, 48)
            self.font_medium = pygame.font.Font(font_path, 32)
            self.font_small = pygame.font.Font(font_path, 24)
        except:
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 24)
    
    def create_buttons(self):
        """Crea los botones del menú"""
        button_width = 300
        button_height = 60
        button_margin = 20
        total_height = (button_height * 3) + (button_margin * 2)
        start_y = (self.screen_height - total_height) // 2 + 50
        
        # Verificar si existe partida guardada
        has_saved_game = self.check_saved_game()
        
        self.buttons = [
            {
                "text": "Nueva Partida",
                "rect": pygame.Rect((self.screen_width - button_width) // 2, start_y, button_width, button_height),
                "action": "new_game",
                "enabled": True
            },
            {
                "text": "Cargar Partida",
                "rect": pygame.Rect((self.screen_width - button_width) // 2, start_y + button_height + button_margin, button_width, button_height),
                "action": "load_game", 
                "enabled": has_saved_game
            },
            {
                "text": "Cerrar Juego",
                "rect": pygame.Rect((self.screen_width - button_width) // 2, start_y + (button_height + button_margin) * 2, button_width, button_height),
                "action": "quit",
                "enabled": True
            }
        ]
    
    def check_saved_game(self):
        """Verifica si existe una partida guardada"""
        try:
            saved_data = load_slot("slot1.sav")
            return saved_data is not None
        except:
            return False
    
    def handle_event(self, event):
        """Maneja los eventos del menú"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_button = (self.selected_button - 1) % len(self.buttons)
                while not self.buttons[self.selected_button]["enabled"]:
                    self.selected_button = (self.selected_button - 1) % len(self.buttons)
            elif event.key == pygame.K_DOWN:
                self.selected_button = (self.selected_button + 1) % len(self.buttons)
                while not self.buttons[self.selected_button]["enabled"]:
                    self.selected_button = (self.selected_button + 1) % len(self.buttons)
            elif event.key == pygame.K_RETURN:
                return self.buttons[self.selected_button]["action"]
        
        elif event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button["rect"].collidepoint(event.pos) and button["enabled"]:
                    self.selected_button = i
                    break
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Click izquierdo
                for button in self.buttons:
                    if button["rect"].collidepoint(event.pos) and button["enabled"]:
                        return button["action"]
        
        return None
    
    def draw(self, screen):
        """Dibuja el menú en la pantalla"""
        # Fondo
        screen.fill(self.bg_color)
        
        # Título
        title_surf = self.font_large.render("COURIER QUEST", True, self.title_color)
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 4))
        screen.blit(title_surf, title_rect)
        
        # Subtítulo
        subtitle_surf = self.font_small.render("Sistema de Entregas Urbanas", True, (200, 200, 200))
        subtitle_rect = subtitle_surf.get_rect(center=(self.screen_width // 2, self.screen_height // 4 + 50))
        screen.blit(subtitle_surf, subtitle_rect)
        
        # Dibujar botones
        for i, button in enumerate(self.buttons):
            color = self.button_hover_color if i == self.selected_button else self.button_color
            if not button["enabled"]:
                color = self.button_disabled_color
            
            # Dibujar botón
            pygame.draw.rect(screen, color, button["rect"], border_radius=10)
            pygame.draw.rect(screen, (255, 255, 255), button["rect"], 2, border_radius=10)
            
            # Texto del botón
            text_color = self.button_text_color if button["enabled"] else (150, 150, 150)
            text_surf = self.font_medium.render(button["text"], True, text_color)
            text_rect = text_surf.get_rect(center=button["rect"].center)
            screen.blit(text_surf, text_rect)
            
            # Indicador de selección (solo para teclado)
            if i == self.selected_button:
                indicator = ">"
                indicator_surf = self.font_medium.render(indicator, True, (255, 255, 0))
                indicator_rect = indicator_surf.get_rect(midright=(button["rect"].left - 10, button["rect"].centery))
                screen.blit(indicator_surf, indicator_rect)
        
        # Información de controles
        controls_text = "Usa las flechas y ENTER o haz clic para seleccionar"
        controls_surf = self.font_small.render(controls_text, True, (150, 150, 150))
        controls_rect = controls_surf.get_rect(center=(self.screen_width // 2, self.screen_height - 50))
        screen.blit(controls_surf, controls_rect)