import pygame
import os

class HUD:
    """
    Heads-Up Display (HUD) - Interfaz de usuario en pantalla.
    
    Muestra información importante del juego como:
    - Tiempo restante, ingresos, reputación
    - Estado del repartidor (stamina, posición)
    - Información del pedido actual
    - Controles y atajos de teclado
    """
    
    # Constantes de diseño y espaciado
    PAD = 20  # Padding general
    VR_GAP = 6  # Espacio vertical entre elementos
    SEC_GAP = 12  # Espacio entre secciones
    DIV_ALPHA = 35  # Transparencia de líneas divisorias
    FOOTER_GAP_LINE = 3  # Espacio entre líneas del footer
    FOOTER_SEC_GAP = 8  # Espacio entre secciones del footer
    FOOTER_GAP_LINE_COMPACT = 2  # Espacio compacto para footer
    FOOTER_SEC_GAP_COMPACT = 6  # Espacio compacto entre secciones
    CARD_H_MIN = 94  # Altura mínima de tarjeta de pedido
    CARD_PAD = 10  # Padding interno de tarjetas
    CARD_BG = (255, 255, 255, 12)  # Fondo semitransparente de tarjetas

    def __init__(self, rect_area, screen_height, tile_size):
        """
        Inicializa el HUD.
        
        Args:
            rect_area: Área rectangular donde se dibujará el HUD
            screen_height: Alto de pantalla para cálculos de posición
            tile_size: Tamaño de tiles para escalado
        """
        self.rect = rect_area  # Área del HUD
        self.screen_height = screen_height
        self.tile_size = tile_size

        # Paleta de colores
        self.bg = (20, 20, 20)  # Fondo oscuro
        self.tx = (255, 255, 255)  # Texto normal
        self.hl = (255, 215, 0)  # Destacado (dorado)
        self.warn = (255, 100, 100)  # Advertencia (rojo)
        self.ok = (100, 255, 100)  # Éxito (verde)
        self.hint = (200, 200, 255)  # Información (azul claro)
        self.sortc = (180, 230, 180)  # Ordenamiento (verde claro)
        self.subtx = (180, 180, 180)  # Texto secundario

        # Cargar fuentes
        self.f_title = self._font(28)  # Título grande
        self.f = self._font(20)  # Texto normal
        self.fs = self._font(16)  # Texto pequeño
        self.fs_small = self._font(14)  # Texto muy pequeño

        # Textos de controles para el footer
        self.controls = [
            "Flechas: Moverse",
            "ESPACIO: Recoger",
            "E: Entregar",
            "TAB: Cambiar pedido",
            "A: Ver pedidos cerca",
        ]
        self.sorting = [
            "F1: Por Prioridad",
            "F2: Por Tiempo",
            "F3: Por Pago",
            "F4: Orden original",
        ]
        self.system = [
            "Ctrl+S: Guardar",
            "Ctrl+L: Cargar",
            "Ctrl+Z: Deshacer"  # Control de deshacer
        ]

    def _font(self, size):
        """
        Carga una fuente con manejo de errores.
        
        Args:
            size: Tamaño de la fuente
            
        Returns:
            Fuente cargada o fuente por defecto si falla
        """
        try:
            return pygame.font.Font(os.path.join("fonts", "RussoOne-Regular.ttf"), size)
        except Exception:
            return pygame.font.Font(None, size)  # Fuente por defecto

    def _blit(self, surf, text, font, col, x, y, align="left"):
        """
        Dibuja texto en una superficie con alineación.
        
        Args:
            surf: Surface donde dibujar
            text: Texto a renderizar
            font: Fuente a usar
            col: Color del texto
            x, y: Posición
            align: Alineación ("left", "center", "right")
            
        Returns:
            Altura del texto renderizado
        """
        s = font.render(text, True, col)
        r = s.get_rect()
        if align == "left":
            r.topleft = (x, y)
        elif align == "center":
            r.midtop = (x, y)
        elif align == "right":
            r.topright = (x, y)
        surf.blit(s, r)
        return r.height

    def _div(self, surf, y):
        """
        Dibuja una línea divisoria.
        
        Returns:
            Altura de la línea (1 pixel)
        """
        line = pygame.Surface((self.rect.width - 2*self.PAD, 1), pygame.SRCALPHA)
        line.fill((255, 255, 255, self.DIV_ALPHA))
        surf.blit(line, (self.rect.left + self.PAD, y))
        return 1

    def _fmt_secs(self, secs: float) -> str:
        """
        Formatea segundos a formato MM:SS.
        
        Returns:
            String en formato "MM:SS"
        """
        secs = max(0, int(secs))
        m = secs // 60
        s = secs % 60
        return f"{m:02d}:{s:02d}"

    def _draw_priority_badge(self, screen, x, y, level: int):
        """
        Dibuja un badge de prioridad con color según nivel.
        
        Returns:
            Altura del badge
        """
        if level >= 2:
            col = (255, 120, 120)  # Rojo para prioridad alta
            txt = "PRIO 2"
        elif level == 1:
            col = (255, 200, 120)  # Naranja para prioridad media
            txt = "PRIO 1"
        else:
            col = (180, 220, 255)  # Azul para prioridad baja
            txt = "PRIO 0"

        pad_h = 4  # Padding vertical
        pad_w = 8  # Padding horizontal
        s = self.fs.render(txt, True, (0, 0, 0))  # Texto negro
        w, h = s.get_width() + pad_w*2, s.get_height() + pad_h*2
        badge = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(badge, col + (180,), pygame.Rect(0, 0, w, h), border_radius=8)
        badge.blit(s, (pad_w, pad_h))
        screen.blit(badge, (x, y))
        return h

    def _draw_footer(self, screen, x, bottom, contextual, f_body, gap_line, sec_gap):
        """
        Dibuja el footer con controles y mensajes contextuales.
        
        Returns:
            Posición Y superior alcanzada
        """
        lh = f_body.get_linesize()  # Altura de línea
        y = bottom

        # Sistema (parte inferior)
        for t in reversed(self.system):
            y -= (lh - gap_line)
            self._blit(screen, t, f_body, self.subtx, x, y)
        y -= sec_gap + lh
        self._blit(screen, "--- Sistema ---", f_body, self.hint, x, y)

        # Ordenar
        for t in reversed(self.sorting):
            y -= (lh - gap_line)
            self._blit(screen, t, f_body, self.sortc, x, y)
        y -= sec_gap + lh
        self._blit(screen, "--- Ordenar ---", f_body, self.sortc, x, y)

        # Controles
        for t in reversed(self.controls):
            y -= (lh - gap_line)
            self._blit(screen, t, f_body, self.subtx, x, y)
        y -= sec_gap + lh
        self._blit(screen, "--- Controles ---", f_body, self.hint, x, y)

        # Mensaje contextual (recoger/entregar)
        if contextual:
            y -= (self.f.get_linesize() + 10)
            color = self.hl if "ESPACIO" in contextual else self.ok
            self._blit(screen, contextual, self.f, color, x, y)

        return y

    def _footer_with_autofit(self, screen, x, bottom, top_limit, contextual):
        """
        Dibuja el footer con autoajuste para evitar superposición.
        
        Returns:
            Posición Y superior alcanzada
        """
        min_gap = 12  # Espacio mínimo requerido
        top = self._draw_footer(
            screen, x, bottom, contextual, self.fs,
            self.FOOTER_GAP_LINE, self.FOOTER_SEC_GAP
        )
        # Si hay superposición, usar versión compacta
        if top < top_limit + min_gap:
            pygame.draw.rect(screen, self.bg,
                             pygame.Rect(self.rect.left, max(top, top_limit),
                                         self.rect.width, bottom - max(top, top_limit)))
            top = self._draw_footer(
                screen, x, bottom, contextual, self.fs_small,
                self.FOOTER_GAP_LINE_COMPACT, self.FOOTER_SEC_GAP_COMPACT
            )
        return top

    def _draw_job_card(self, screen, x, y, w, job, current_game_time=None):
        """
        Dibuja una tarjeta con información del pedido actual.
        
        Returns:
            Posición Y inferior de la tarjeta
        """
        card_h = self.CARD_H_MIN
        card_rect = pygame.Rect(x, y, w, card_h)
        s = pygame.Surface((w, card_h), pygame.SRCALPHA)
        s.fill(self.CARD_BG)  # Fondo semitransparente
        screen.blit(s, (x, y))

        yy = y + self.CARD_PAD  # Posición Y actual dentro de la tarjeta
        
        # Título de la tarjeta
        yy += self._blit(screen, "PEDIDO ACTUAL:", self.f, self.hl, x + self.CARD_PAD, yy)
        
        # Badge de prioridad
        try:
            prio = int(getattr(job, "priority", 0))
        except Exception:
            prio = 0
        self._draw_priority_badge(screen, x + w - self.CARD_PAD - 92, yy - self.f.get_linesize() + 2, prio)

        # Información del pedido
        yy += self._blit(screen, f"ID: {job.id}", self.f, self.tx, x + self.CARD_PAD, yy)
        yy += self._blit(screen, f"Pago: ${job.payout:.1f}", self.f, self.tx, x + self.CARD_PAD, yy)

        # Tiempo restante si está disponible
        if current_game_time is not None and hasattr(job, "get_time_until_deadline"):
            try:
                tl = float(job.get_time_until_deadline(current_game_time))
                tcol = self.warn if tl <= 0 else (self.hl if tl < 60 else self.tx)
                yy += self._blit(screen, f"Tiempo restante: {self._fmt_secs(tl)}", self.f, tcol, x + self.CARD_PAD, yy)
            except Exception:
                pass

        return card_rect.bottom

    def draw(self, screen, courier, weather_condition, speed_multiplier,
             remaining_time=0, goal_income=0, near_pickup=False, near_dropoff=False,
             current_game_time=None, current_surface_weight=1.0):
        """
        Dibuja todo el HUD en la pantalla.
        
        Args:
            screen: Surface donde dibujar
            courier: Objeto repartidor con estadísticas
            weather_condition: Condición climática actual
            speed_multiplier: Multiplicador de velocidad por clima
            remaining_time: Tiempo restante de partida
            goal_income: Meta de ingresos a alcanzar
            near_pickup: Si está cerca de punto de recogida
            near_dropoff: Si está cerca de punto de entrega
            current_game_time: Tiempo actual del juego
            current_surface_weight: Peso de la superficie actual
        """
        # Fondo del HUD
        pygame.draw.rect(screen, self.bg, self.rect)
        
        # Configuración de posición inicial
        pad = self.PAD
        x = self.rect.left + pad
        y = self.rect.top + pad
        content_w = self.rect.width - 2*pad

        # --- Título ---
        y += self._blit(screen, "COURIER QUEST", self.f_title, self.hl,
                        self.rect.centerx, y, align="center") + self.SEC_GAP

        # Tiempo / Ingresos
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        tcol = self.warn if remaining_time < 60 else self.tx  # Rojo si poco tiempo
        y += self._blit(screen, f"Tiempo: {minutes:02d}:{seconds:02d}", self.f, tcol, x, y) + self.VR_GAP
        
        icol = self.ok if courier.income >= goal_income else self.tx  # Verde si meta alcanzada
        y += self._blit(screen, f"Ingresos: ${courier.income:.1f}/{int(goal_income)}", self.f, icol, x, y)
        y += self.SEC_GAP + self._div(screen, y)

        # --- Repartidor ---
        y += self.SEC_GAP
        y += self._blit(screen, "--- Repartidor ---", self.fs, self.tx, x, y)
        y += self.VR_GAP
        y += self._blit(screen, f"Posición: ({courier.x}, {courier.y})", self.fs, self.tx, x, y)
        
        delivered = getattr(courier, "packages_delivered", getattr(courier, "delivered_count", 0))
        y += self._blit(screen, f"Entregados: {delivered}", self.fs, self.tx, x, y)

        # Barra de resistencia
        max_sta = max(1, int(getattr(courier, "max_stamina", 100)))
        sta_pct = max(0.0, min(1.0, courier.stamina / max_sta))
        bar_h = 20
        bar_rect = pygame.Rect(x, y + self.VR_GAP, content_w, bar_h)
        pygame.draw.rect(screen, (50, 50, 50), bar_rect)  # Fondo gris
        fill_rect = pygame.Rect(x, y + self.VR_GAP, int(content_w * sta_pct), bar_h)
        pygame.draw.rect(screen, self.warn if sta_pct < 0.3 else self.ok, fill_rect)  # Rojo si poca stamina
        y = bar_rect.bottom + 4
        y += self._blit(screen, f"Resistencia: {int(courier.stamina)}/{max_sta}",
                        self.fs, self.tx, x + content_w//2, y, align="center")
        y += self.SEC_GAP + self._div(screen, y)

        # Reputación
        y += self.SEC_GAP
        rep = int(getattr(courier, "reputation", 70))
        rcol = self.ok if rep >= 90 else self.warn if rep < 30 else self.tx
        y += self._blit(screen, f"Reputación: {rep}", self.f, rcol, x, y)
        y += self.SEC_GAP + self._div(screen, y)

        # Inventario
        y += self.SEC_GAP
        y += self._blit(screen, "--- Inventario ---", self.fs, self.tx, x, y)
        if hasattr(courier, "has_jobs") and courier.has_jobs():
            y += self._blit(screen, "Tienes pedidos activos", self.fs, self.hl, x, y)
        else:
            y += self._blit(screen, "Sin pedidos", self.fs, (150, 150, 150), x, y)
        y += self.SEC_GAP + self._div(screen, y)

        # Clima
        y += self.SEC_GAP
        y += self._blit(screen, "--- Clima ---", self.fs, self.tx, x, y)
        weather_display = str(weather_condition).replace("_", " ").title()
        y += self.VR_GAP
        y += self._blit(screen, f"Condición: {weather_display}", self.fs, self.tx, x, y)
        y += self._blit(screen, f"Velocidad: {int(speed_multiplier*100)}%", self.fs, self.tx, x, y)
        
        # Efecto de superficie actual
        y += self._blit(screen, f"Superficie: {int(current_surface_weight*100)}%", self.fs, self.tx, x, y)

        # --- FOOTER y CARD ---
        bottom = self.rect.bottom - self.PAD
        contextual = None
        
        # Mensajes contextuales según proximidad
        if near_pickup:
            contextual = "🟡 Presiona ESPACIO para recoger"
        elif near_dropoff:
            contextual = "🟢 Presiona E para entregar"

        # Dibujar footer con autoajuste
        est_top = self._draw_footer(screen, x, bottom, contextual, self.fs,
                                    self.FOOTER_GAP_LINE, self.FOOTER_SEC_GAP)
        pygame.draw.rect(screen, self.bg,
                         pygame.Rect(self.rect.left, est_top, self.rect.width, bottom - est_top))

        # Tarjeta de pedido actual si hay espacio
        if hasattr(courier, "has_jobs") and courier.has_jobs():
            job = courier.get_current_job()
            if job and (est_top - y) > self.CARD_H_MIN + self.SEC_GAP:
                y += self.SEC_GAP
                y = self._draw_job_card(screen, x, y, content_w, job, current_game_time=current_game_time)
                y += self.SEC_GAP
                y += self._div(screen, y)

        top_limit = max(y + 4, self.rect.top + self.PAD + 4)
        self._footer_with_autofit(screen, x, bottom, top_limit, contextual)