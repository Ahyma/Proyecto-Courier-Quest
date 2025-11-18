# game/menu.py
"""
import pygame es necesario para el menú gráfico
from game.ai_courier import AIDifficulty es necesario para manejar la dificultad de la IA
from game.score_board import load_scores es necesario para cargar las puntuaciones guardadas
""" 
import pygame

from game.ai_courier import AIDifficulty
from game.score_board import load_scores


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

    """ 
    Inicializa el menú con la pantalla dada
    Parámetros:
      - screen: la superficie de pygame donde se dibuja el menú
    """ 
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        pygame.font.init()
        self.title_font = pygame.font.SysFont("arial", 64, bold=True)
        self.button_font = pygame.font.SysFont("arial", 32, bold=True)
        self.small_font = pygame.font.SysFont("arial", 20, bold=False)

        self.buttons = []
        self._build_buttons()

    """ 
    Construye los botones del menú con sus posiciones y acciones
    """ 
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
            ("Puntuaciones", "scores_screen"),
            ("Salir", "exit"),
        ]

        self.buttons = []
        for i, (label, action) in enumerate(labels_actions):
            x = center_x - button_width // 2
            y = start_y + i * (button_height + margin)
            rect = pygame.Rect(x, y, button_width, button_height)
            self.buttons.append({"rect": rect, "label": label, "action": action})

    """ 
    Se les pone @staticmethod porque no usan self
    Convierte la dificultad de la IA a texto legible
    """ 
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

    # ---------- PANTALLA DE PUNTUACIONES ----------
    """ 
    _format_timestamp: Convierte un timestamp ISO a un formato corto yyyy-mm-dd hh:mm
    _scores_screen: Muestra la pantalla de puntuaciones y maneja la navegación
    Devuelve True si el usuario cerró la ventana (QUIT), False si solo volvió al menú con ESC
    """ 
    def _format_timestamp(self, ts: str) -> str:
        """Convierte el ISO a algo corto yyyy-mm-dd hh:mm. Si falla, devuelve el raw."""
        if not ts:
            return ""
        try:
            # Reemplazar 'Z' por '+00:00' si viene en ese formato
            if ts.endswith("Z"):
                ts = ts[:-1] + "+00:00"
            from datetime import datetime
            dt = datetime.fromisoformat(ts)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return ts

    def _scores_screen(self) -> bool:
        """
        Muestra la pantalla de puntuaciones.
        Devuelve True si el usuario cerró la ventana (QUIT),
        False si solo volvió al menú con ESC.
        """
        clock = pygame.time.Clock()

        # Cargar todos los scores ordenados
        scores = load_scores()

        offset = 0           # índice de inicio visible
        max_visible = 10     # cuántas filas mostrar a la vez

        """ 
        Bucle principal de la pantalla de puntuaciones
        Maneja eventos de teclado para desplazarse y volver al menú
        """ 
        running_scores = True
        while running_scores:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Cerrar juego completamente
                    return True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Volver al menú principal
                        running_scores = False
                    elif event.key == pygame.K_UP:
                        if offset > 0:
                            offset -= 1
                    elif event.key == pygame.K_DOWN:
                        if offset + max_visible < len(scores):
                            offset += 1

            # Fondo
            self.screen.fill((30, 30, 30))

            # Título
            title_surface = self.title_font.render("Puntuaciones", True, (255, 255, 255))
            title_rect = title_surface.get_rect(center=(self.width // 2, 80))
            self.screen.blit(title_surface, title_rect)

            # Subtítulo / instrucciones
            info_text = "ESC: volver | ↑/↓: desplazarse" if scores else "ESC: volver"
            info_surface = self.small_font.render(info_text, True, (200, 200, 200))
            info_rect = info_surface.get_rect(center=(self.width // 2, 130))
            self.screen.blit(info_surface, info_rect)

            # Cabecera de columnas
            header_y = 180
            header_x = 120
            headers = ["#", "Score", "Ingresos", "Tiempo (s)", "Reputación", "Fecha"]
            col_widths = [40, 100, 120, 130, 120, 240]

            x = header_x
            for i, h in enumerate(headers):
                h_surf = self.small_font.render(h, True, (220, 220, 220))
                self.screen.blit(h_surf, (x, header_y))
                x += col_widths[i]

            # Línea separadora
            pygame.draw.line(
                self.screen,
                (120, 120, 120),
                (header_x, header_y + 24),
                (header_x + sum(col_widths), header_y + 24),
                1,
            )

            # Contenido
            list_y_start = header_y + 36

            if not scores:
                # Mensaje si no hay puntajes aún
                msg_surface = self.small_font.render("No hay puntuaciones guardadas todavía.", True, (200, 200, 200))
                msg_rect = msg_surface.get_rect(center=(self.width // 2, list_y_start + 40))
                self.screen.blit(msg_surface, msg_rect)
            else:
                # Mostrar sólo el segmento visible
                visible_scores = scores[offset: offset + max_visible]
                row_y = list_y_start

                for idx, entry in enumerate(visible_scores, start=offset + 1):
                    score = entry.get("score", 0.0)
                    income = entry.get("income", 0.0)
                    time_s = entry.get("time", 0.0)
                    rep = entry.get("reputation", 0)
                    ts = self._format_timestamp(entry.get("timestamp", ""))

                    # Color alternado de filas
                    if idx % 2 == 0:
                        row_bg = (40, 40, 40)
                    else:
                        row_bg = (50, 50, 50)
                    pygame.draw.rect(
                        self.screen,
                        row_bg,
                        pygame.Rect(header_x - 10, row_y - 4, sum(col_widths) + 20, 28),
                    )

                    # Preparar cada columna
                    values = [
                        str(idx),
                        f"{score:.2f}",
                        f"{income:.2f}",
                        f"{time_s:.1f}",
                        str(rep),
                        ts,
                    ]

                    x = header_x
                    for i, val in enumerate(values):
                        v_surf = self.small_font.render(val, True, (230, 230, 230))
                        self.screen.blit(v_surf, (x, row_y))
                        x += col_widths[i]

                    row_y += 30  # siguiente fila

                # Indicador de página / offset
                page_info = f"{offset + 1}-{min(offset + max_visible, len(scores))} de {len(scores)}"
                page_surf = self.small_font.render(page_info, True, (200, 200, 200))
                page_rect = page_surf.get_rect(center=(self.width // 2, self.height - 40))
                self.screen.blit(page_surf, page_rect)

            pygame.display.flip()
            clock.tick(60)

        # Volver al menú sin cerrar el juego
        return False

    # ---------- LOOP PRINCIPAL DEL MENÚ ----------
    """ 
    show: Bucle del menú
    Devuelve (action, difficulty)

    Primero inicializa el reloj y variables
    luego entra en un bucle donde maneja eventos:
    - QUIT: devuelve "exit"
    - Clic en botón: dependiendo del botón, cambia dificultad, entra a puntuaciones o devuelve la acción
    """ 

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
                            elif btn["action"] == "scores_screen":
                                # Entrar a la pantalla de puntuaciones
                                quit_game = self._scores_screen()
                                if quit_game:
                                    return "exit", difficulty
                                # Si no se cerró la ventana, simplemente seguimos en el menú
                            else:
                                return btn["action"], difficulty

            # Fondo gris
            self.screen.fill((200, 200, 200))

            # Título
            title_surface = self.title_font.render("Courier Quest II", True, (0, 0, 0))
            title_rect = title_surface.get_rect(center=(self.width // 2, 120))
            self.screen.blit(title_surface, title_rect)

            # -------- ESTADO DEL MOUSE PARA HOVER / CLICK VISUAL --------
            """ 
            Primero obtiene la posición del mouse y si el botón izquierdo está presionado
            Luego itera sobre los botones para dibujarlos:
            - Determina el color base según el tipo de botón (rojo para salir, gris para otros)
            - Cambia el color si está en hover o presionado
            - Dibuja el rectángulo del botón
            - Dibuja el texto del botón centrado
            """ 
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()[0]  # True si botón izquierdo está presionado

            # Botones
            for btn in self.buttons:
                rect = btn["rect"]

                # Base por tipo de botón
                if btn["action"] == "exit":
                    base_color = (200, 0, 0)
                else:
                    base_color = (60, 60, 60)

                # Hover / pressed
                is_hover = rect.collidepoint(mouse_pos)
                is_pressed = is_hover and mouse_pressed

                if is_pressed:
                    color = (
                        max(base_color[0] - 40, 0),
                        max(base_color[1] - 40, 0),
                        max(base_color[2] - 40, 0),
                    )
                elif is_hover:
                    color = (
                        min(base_color[0] + 40, 255),
                        min(base_color[1] + 40, 255),
                        min(base_color[2] + 40, 255),
                    )
                else:
                    color = base_color

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
