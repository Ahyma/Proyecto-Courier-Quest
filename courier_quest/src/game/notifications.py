# courier_quest/src/game/notifications.py
import pygame
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Toast:
    """
    Representa una notificación temporal en pantalla.
    
    Attributes:
        text: El mensaje a mostrar
        color: Color RGB del texto
        ttl: Tiempo de vida restante en segundos
        max_ttl: Duración total original para calcular fade out
        icon: Opcional, emoji o carácter que acompaña al texto
    """
    text: str
    color: Tuple[int, int, int]
    ttl: float            # segundos restantes
    max_ttl: float        # duración total (para calcular alpha)
    icon: str | None = None  # opcional: emoji/char

class NotificationsOverlay:
    """
    Sistema de notificaciones superpuestas (toasts) que no bloquean el juego.
    
    Características:
    - Se apilan automáticamente
    - Hacen fade out cuando expiran
    - No requieren assets externos, usan fuentes de pygame
    - No bloquean la entrada del usuario
    """
    
    def __init__(self, panel_width: int, screen_height: int, font_path: str | None = None):
        """
        Inicializa el sistema de notificaciones.
        
        Args:
            panel_width: Ancho del panel donde se mostrarán las notificaciones
            screen_height: Alto de la pantalla para posicionamiento
            font_path: Ruta opcional a la fuente, usa una por defecto si no se especifica
        """
        self.toasts: List[Toast] = []  # Lista de notificaciones activas
        self.pad = 10  # Padding interno
        self.line_gap = 6  # Espacio entre notificaciones
        self.card_pad = 10  # Padding dentro de cada tarjeta de notificación
        self.card_alpha = 180  # Opacidad base de las tarjetas
        self.card_bg = (20, 20, 20)  # Color de fondo (se mezcla con alpha)
        self.max_width = panel_width - 2 * self.pad  # Ancho máximo para las notificaciones

        # Cargar fuente, usar por defecto si falla
        try:
            self.font = pygame.font.Font(font_path or "fonts/RussoOne-Regular.ttf", 18)
        except Exception:
            self.font = pygame.font.Font(None, 18)

        # Configuración de posicionamiento (esquina superior derecha)
        self.anchor_x = 0
        self.anchor_y = 0
        self.screen_h = screen_height

    def add(self, text: str, color=(255, 255, 255), duration: float = 2.5, icon: str | None = None):
        """
        Agrega una nueva notificación.
        
        Args:
            text: Mensaje a mostrar
            color: Color del texto (RGB)
            duration: Duración en segundos
            icon: Icono opcional (emoji)
        """
        # Limitar la cola para evitar overflow visual
        if len(self.toasts) > 10:
            self.toasts.pop(0)  # Eliminar la notificación más antigua
            
        # Crear y agregar nueva notificación
        self.toasts.append(Toast(text=text, color=color, ttl=duration, max_ttl=duration, icon=icon))

    # Métodos de conveniencia para tipos específicos de notificaciones

    def success(self, text: str, duration: float = 2.5):
        """Notificación de éxito (verde con check)"""
        self.add(text, color=(120, 255, 120), duration=duration, icon="✅")

    def info(self, text: str, duration: float = 2.5):
        """Notificación informativa (azul claro con 'i')"""
        self.add(text, color=(200, 220, 255), duration=duration, icon="ℹ")

    def warn(self, text: str, duration: float = 2.8):
        """Notificación de advertencia (amarillo con triángulo)"""
        self.add(text, color=(255, 220, 120), duration=duration, icon="⚠")

    def error(self, text: str, duration: float = 3.0):
        """Notificación de error (rojo con prohibido)"""
        self.add(text, color=(255, 120, 120), duration=duration, icon="⛔")

    def update(self, dt: float):
        """
        Actualiza el estado de las notificaciones.
        
        Args:
            dt: Tiempo delta desde la última actualización
        """
        # Reducir TTL de todas las notificaciones
        for t in self.toasts:
            t.ttl -= dt
            
        # Eliminar notificaciones que han expirado
        self.toasts = [t for t in self.toasts if t.ttl > 0]

    def _render_line(self, text: str, color: Tuple[int, int, int]):
        """
        Renderiza una línea de texto.
        
        Returns:
            Tupla con (surface, rect) del texto renderizado
        """
        surf = self.font.render(text, True, color)
        return surf, surf.get_rect()

    def draw(self, screen: pygame.Surface, panel_rect: pygame.Rect):
        """
        Dibuja todas las notificaciones activas en el panel.
        
        Args:
            screen: Surface donde dibujar
            panel_rect: Rectángulo del panel HUD
        """
        if not self.toasts:
            return  # No hay notificaciones que mostrar

        # Posicionamiento inicial (esquina superior derecha del panel)
        x_right = panel_rect.right - self.pad
        y = panel_rect.top + self.pad

        # Dibujar de más reciente a más antigua (de arriba hacia abajo)
        for toast in reversed(self.toasts):
            # Componer texto con icono si existe
            txt = f"{toast.icon} {toast.text}" if toast.icon else toast.text

            # Renderizar texto y calcular tamaño de tarjeta
            text_surf, text_rect = self._render_line(txt, toast.color)
            card_w = min(self.max_width, text_rect.width + 2 * self.card_pad)
            card_h = text_rect.height + 2 * self.card_pad

            # Calcular alpha para fade out (último 40% del TTL)
            alpha_ratio = max(0.0, min(1.0, toast.ttl / max(0.0001, toast.max_ttl)))
            if alpha_ratio < 0.4:
                a = int(self.card_alpha * (alpha_ratio / 0.4))  # Fade out progresivo
            else:
                a = self.card_alpha  # Opacidad completa

            # Crear y dibujar fondo de la tarjeta con alpha
            card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            card.fill((*self.card_bg, a))
            screen.blit(card, (x_right - card_w, y))

            # Dibujar texto sobre la tarjeta
            text_x = x_right - card_w + self.card_pad
            text_y = y + self.card_pad
            screen.blit(text_surf, (text_x, text_y))

            # Mover posición Y para la siguiente notificación
            y += card_h + self.line_gap