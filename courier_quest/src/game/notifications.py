# courier_quest/src/game/notifications.py
import pygame
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Toast:
    text: str
    color: Tuple[int, int, int]
    ttl: float            # segundos restantes
    max_ttl: float        # duración total (para calcular alpha)
    icon: str | None = None  # opcional: emoji/char

class NotificationsOverlay:
    """
    Overlay simple de 'toasts' (notificaciones) apiladas.
    - No bloquea input
    - Fade out automático
    - No requiere assets extra; usa pygame fonts
    """
    def __init__(self, panel_width: int, screen_height: int, font_path: str | None = None):
        self.toasts: List[Toast] = []
        self.pad = 10
        self.line_gap = 6
        self.card_pad = 10
        self.card_alpha = 180
        self.card_bg = (20, 20, 20)  # se mezcla con alpha
        self.max_width = panel_width - 2 * self.pad

        try:
            self.font = pygame.font.Font(font_path or "fonts/RussoOne-Regular.ttf", 18)
        except Exception:
            self.font = pygame.font.Font(None, 18)

        # Posicionado: esquina superior derecha del HUD/panel
        self.anchor_x = 0
        self.anchor_y = 0
        self.screen_h = screen_height

    def add(self, text: str, color=(255, 255, 255), duration: float = 2.5, icon: str | None = None):
        # Limitar cola para evitar overflow visual
        if len(self.toasts) > 10:
            self.toasts.pop(0)
        self.toasts.append(Toast(text=text, color=color, ttl=duration, max_ttl=duration, icon=icon))

    # Atajos de semántica
    def success(self, text: str, duration: float = 2.5):
        self.add(text, color=(120, 255, 120), duration=duration, icon="✅")

    def info(self, text: str, duration: float = 2.5):
        self.add(text, color=(200, 220, 255), duration=duration, icon="ℹ")

    def warn(self, text: str, duration: float = 2.8):
        self.add(text, color=(255, 220, 120), duration=duration, icon="⚠")

    def error(self, text: str, duration: float = 3.0):
        self.add(text, color=(255, 120, 120), duration=duration, icon="⛔")

    def update(self, dt: float):
        # Consumir TTL; borrar expirados
        for t in self.toasts:
            t.ttl -= dt
        self.toasts = [t for t in self.toasts if t.ttl > 0]

    def _render_line(self, text: str, color: Tuple[int, int, int]):
        surf = self.font.render(text, True, color)
        return surf, surf.get_rect()

    def draw(self, screen: pygame.Surface, panel_rect: pygame.Rect):
        """
        Dibuja las tarjetas apiladas dentro del panel (HUD), arriba a la derecha.
        """
        if not self.toasts:
            return

        x_right = panel_rect.right - self.pad
        y = panel_rect.top + self.pad

        # Se dibujan de más reciente a más antigua (arriba → abajo)
        for toast in reversed(self.toasts):
            # Componer texto (icono + mensaje)
            txt = f"{toast.icon} {toast.text}" if toast.icon else toast.text

            # Render de texto y tarjeta con padding
            text_surf, text_rect = self._render_line(txt, toast.color)
            card_w = min(self.max_width, text_rect.width + 2 * self.card_pad)
            card_h = text_rect.height + 2 * self.card_pad

            # Alpha dinámico por fade (último 40% del ttl)
            alpha_ratio = max(0.0, min(1.0, toast.ttl / max(0.0001, toast.max_ttl)))
            if alpha_ratio < 0.4:
                a = int(self.card_alpha * (alpha_ratio / 0.4))
            else:
                a = self.card_alpha

            # Fondo con alpha
            card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            card.fill((*self.card_bg, a))
            screen.blit(card, (x_right - card_w, y))

            # Texto
            text_x = x_right - card_w + self.card_pad
            text_y = y + self.card_pad
            screen.blit(text_surf, (text_x, text_y))

            y += card_h + self.line_gap