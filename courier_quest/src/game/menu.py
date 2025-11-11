import pygame
from game.palette import WHITE, BLACK, BLUE, LIGHT_GRAY, DARK_GRAY, RED
# Importamos AIDifficulty, asumiendo que ya está en game/ai_courier.py
from game.ai_courier import AIDifficulty 

# ----------------------------------------------------------------------
# Elemento UI Básico
# ----------------------------------------------------------------------
class MenuItem:
    """
    Clase base para elementos interactivos del menú (botones).
    """
    def __init__(self, rect, text, action=None, color=DARK_GRAY, text_color=WHITE):
        self.rect = rect
        self.text = text
        self.action = action
        self.color = color
        self.text_color = text_color
        self.is_hovered = False

    def draw(self, screen, font):
        """Dibuja el elemento."""
        # Cambia el color si el mouse está sobre el elemento
        color = BLUE if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        
        # Dibuja el texto centrado
        text_surface = font.render(self.text, True, self.text_color)
        screen.blit(text_surface, text_surface.get_rect(center=self.rect.center))

    def handle_event(self, event):
        """Maneja los eventos (mouse-click)."""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return self.action
        return None

# ----------------------------------------------------------------------
# Selector de Dificultad
# ----------------------------------------------------------------------
class DifficultySelector(MenuItem):
    """
    Un selector de dificultad que cicla entre los niveles de AIDifficulty al hacer clic.
    """
    def __init__(self, rect, initial_difficulty, action_prefix):
        # La acción se define en _update_text
        super().__init__(rect, "", action=action_prefix, color=DARK_GRAY)
        self.difficulties = [d for d in AIDifficulty] # [EASY, MEDIUM, HARD]
        self.current_difficulty = initial_difficulty
        self._update_text()
        
    def _update_text(self):
        """Actualiza el texto para mostrar la dificultad actual (e.g., 'Dificultad IA: Medio')."""
        self.text = f"Dificultad IA: {self.current_difficulty.value}"
        
    def handle_event(self, event):
        """Cambia a la siguiente dificultad al hacer clic."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                # Encuentra el índice actual y pasa al siguiente
                try:
                    current_index = self.difficulties.index(self.current_difficulty)
                except ValueError:
                    current_index = 0 
                    
                new_index = (current_index + 1) % len(self.difficulties)
                self.current_difficulty = self.difficulties[new_index]
                self._update_text()
                
                # Retorna un diccionario para que MainMenu guarde el nuevo valor
                return {
                    "action": self.action, 
                    "value": self.current_difficulty
                }
        
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        
        return None
        
    def get_current_difficulty(self):
        """Retorna el objeto AIDifficulty actual."""
        return self.current_difficulty

# ----------------------------------------------------------------------
# Menú Principal
# ----------------------------------------------------------------------
class MainMenu:
    """
    Menú principal del juego, gestionando el estado y la navegación.
    Incluye el selector de dificultad para la IA antes de iniciar la partida.
    """
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font_large = pygame.font.Font(None, 74)
        self.font_medium = pygame.font.Font(None, 36)
        
        # Configuración por defecto de la IA
        self.ai_difficulty = AIDifficulty.MEDIUM 
        
        # Elementos del menú
        self.main_elements = self._create_main_elements()

    def _create_main_elements(self):
        """Crea los elementos del menú principal."""
        center_x = self.width // 2
        elements = []
        
        # 1. Selector de Dificultad (Posición superior)
        rect_difficulty = pygame.Rect(center_x - 150, self.height // 3 - 50, 300, 50)
        self.difficulty_selector = DifficultySelector(
            rect_difficulty, 
            self.ai_difficulty, 
            action_prefix="set_difficulty"
        )
        elements.append(self.difficulty_selector)
        
        # 2. Botón de Nueva Partida (Inicia el juego con la dificultad seleccionada)
        rect_new = pygame.Rect(center_x - 150, self.height // 3 + 20, 300, 50)
        elements.append(MenuItem(rect_new, "Nueva Partida", action="start_game"))
        
        # 3. Cargar Partida
        rect_load = pygame.Rect(center_x - 150, self.height // 3 + 90, 300, 50)
        elements.append(MenuItem(rect_load, "Cargar Partida", action="load_game"))
        
        # 4. Puntuaciones
        rect_score = pygame.Rect(center_x - 150, self.height // 3 + 160, 300, 50)
        elements.append(MenuItem(rect_score, "Puntuaciones", action="scores"))
        
        # 5. Salir
        rect_quit = pygame.Rect(center_x - 150, self.height // 3 + 230, 300, 50)
        elements.append(MenuItem(rect_quit, "Salir", action="quit", color=RED))
        
        return elements

    def draw(self, screen):
        """Dibuja el menú principal."""
        screen.fill(LIGHT_GRAY)
        
        # Título principal
        title_surface = self.font_large.render("Courier Quest II", True, BLACK)
        screen.blit(title_surface, title_surface.get_rect(center=(self.width // 2, 100)))
        
        # Dibuja todos los elementos (incluyendo el selector de dificultad)
        for item in self.main_elements:
            item.draw(screen, self.font_medium)
            
    def handle_event(self, event):
        """
        Maneja los eventos del menú.
        
        Retorna:
            Diccionario con "action" y opcionalmente "difficulty" si el juego
            debe iniciar, o None si es una interacción interna.
        """
        for item in self.main_elements:
            action_result = item.handle_event(event)
            
            if action_result:
                
                # Caso 1: El selector de dificultad cambia (retorna un diccionario)
                if isinstance(action_result, dict):
                    action = action_result.get("action")
                    if action == "set_difficulty":
                        self.ai_difficulty = action_result.get("value")
                        return None # Interacción interna (se mantiene en el menú)
                
                # Caso 2: Un botón de acción es presionado (retorna una cadena)
                elif isinstance(action_result, str):
                    
                    if action_result == "start_game":
                        # Iniciar juego, retornando la dificultad seleccionada
                        return {
                            "action": "start_game",
                            "difficulty": self.ai_difficulty
                        }
                    
                    # Otras acciones (Cargar, Puntuaciones, Salir)
                    return {"action": action_result} 
        
        return None