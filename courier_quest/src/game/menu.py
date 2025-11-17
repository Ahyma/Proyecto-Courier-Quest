# game/menu.py
import pygame

from game.ai_courier import AIDifficulty


# ==================== MENÚ PRINCIPAL ====================

class Menu:
    """
    Menú principal tipo:
      Courier Quest II
      [Dificultad IA: ...]
      [Nueva partida]
      [Cargar partida]
      [Puntuaciones]
      [Salir]
    """

    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        pygame.font.init()
        self.title_font = pygame.font.SysFont("arial", 64, bold=True)
        self.button_font = pygame.font.SysFont("arial", 32, bold=True)

        self.buttons = []
        self._build_buttons()

    def _build_buttons(self):
        center_x = self.width // 2
        start_y = self.height // 2 - 140
        button_width = 360
        button_height = 56
        margin = 20

        labels_actions = [
            ("Dificultad IA", "toggle_difficulty"),
            ("Nueva Partida", "new_game"),
            ("Cargar Partida", "load_game"),
            ("Puntuaciones", "show_scores"),
            ("Salir", "exit"),
        ]

        self.buttons = []
        for i, (label, action) in enumerate(labels_actions):
            x = center_x - button_width // 2
            y = start_y + i * (button_height + margin)
            rect = pygame.Rect(x, y, button_width, button_height)
            self.buttons.append({"rect": rect, "label": label, "action": action})

    @staticmethod
    def _difficulty_to_text(diff: AIDifficulty) -> str:
        if diff == AIDifficulty.EASY:
            return "EASY"
        if diff == AIDifficulty.HARD:
            return "HARD"
        return "MEDIUM"

    @staticmethod
    def _next_difficulty(diff: AIDifficulty) -> AIDifficulty:
        if diff == AIDifficulty.EASY:
            return AIDifficulty.MEDIUM
        if diff == AIDifficulty.MEDIUM:
            return AIDifficulty.HARD
        return AIDifficulty.EASY

    def show(self, current_difficulty: AIDifficulty):
        """
        Bucle del menú.
        Devuelve (action, difficulty).
        """
        clock = pygame.time.Clock()
        running = True
        difficulty = current_difficulty

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit", difficulty
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    for btn in self.buttons:
                        if btn["rect"].collidepoint(mx, my):
                            if btn["action"] == "toggle_difficulty":
                                difficulty = self._next_difficulty(difficulty)
                            else:
                                return btn["action"], difficulty

            # Fondo gris
            self.screen.fill((200, 200, 200))

            # Título
            title_surface = self.title_font.render("Courier Quest II", True, (0, 0, 0))
            title_rect = title_surface.get_rect(center=(self.width // 2, 120))
            self.screen.blit(title_surface, title_rect)

            # Botones
            for btn in self.buttons:
                rect = btn["rect"]
                color = (60, 60, 60)
                if btn["action"] == "exit":
                    color = (200, 0, 0)

                pygame.draw.rect(self.screen, color, rect, border_radius=6)

                if btn["action"] == "toggle_difficulty":
                    text = f"Dificultad IA: {self._difficulty_to_text(difficulty)}"
                else:
                    text = btn["label"]

                text_surf = self.button_font.render(text, True, (255, 255, 255))
                text_rect = text_surf.get_rect(center=rect.center)
                self.screen.blit(text_surf, text_rect)

            pygame.display.flip()
            clock.tick(60)

        return None, difficulty
