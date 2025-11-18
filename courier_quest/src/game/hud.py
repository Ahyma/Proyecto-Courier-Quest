"""
import pygame es la librería principal para gráficos y manejo de eventos
import os es para manejar rutas de archivos
"""
import pygame
import os

"""
La clase HUD gestiona la interfaz de usuario del juego, mostrando información relevante como
tiempo restante, ingresos, estado del courier, clima, y controles disponibles

Tiene metodos de ayuda para renderizar texto, barras de estado, divisores, y tarjetas de pedidos además de
manejar la presentación de la dificultad de la IA
"""
class HUD:
    PAD = 20
    VR_GAP = 6
    SEC_GAP = 12
    DIV_ALPHA = 35
    FOOTER_GAP_LINE = 3
    FOOTER_SEC_GAP = 8
    FOOTER_GAP_LINE_COMPACT = 2
    FOOTER_SEC_GAP_COMPACT = 6
    CARD_H_MIN = 94
    CARD_PAD = 10
    CARD_BG = (255, 255, 255, 12)

    """
    Inicializa la HUD con el área de rectángulo dada, altura de pantalla, tamaño de tile y dificultad IA opcional
    ---------Parameters---------    
    rect_area : pygame.Rect
        Área rectangular donde se dibuja la HUD
    screen_height : int
        Altura de la pantalla del juego
    tile_size : int
        Tamaño de cada tile en píxeles
    ai_difficulty : Optional[Union[str, Enum]], optional
        Dificultad de la IA, por defecto None
    ---------Returns---------
        __init__: Inicializa la instancia de HUD con los parámetros dados
    """
    def __init__(self, rect_area, screen_height, tile_size, ai_difficulty=None):
        self.rect = rect_area
        self.screen_height = screen_height
        self.tile_size = tile_size

        # Dificultad IA (Enum o string)
        self.ai_difficulty = ai_difficulty

        # Colores base
        self.bg = (20, 20, 20)
        self.tx = (255, 255, 255)
        self.hl = (255, 215, 0)
        self.warn = (255, 100, 100)
        self.ok = (100, 255, 100)
        self.hint = (200, 200, 255)
        self.sortc = (180, 230, 180)
        self.subtx = (180, 180, 180)

        # Colores diferenciados por agente
        # Jugador humano
        self.player_col = (180, 220, 255)
        # IA (CPU)
        self.ai_col = (255, 200, 150)

        # Fuentes
        self.f_title = self._font(28)
        self.f = self._font(20)
        self.fs = self._font(16)
        self.fs_small = self._font(14)

        # Footer
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
        ]

    """
    Métodos de ayuda para renderizar texto, divisores, tarjetas de pedidos, y manejar la dificultad IA
    ---------Parameters---------
    surf : pygame.Surface
        Superficie donde se dibuja el texto o elementos gráficos
    text : str
        Texto a renderizar
    font : pygame.font.Font
        Fuente a utilizar para renderizar el texto
    col : Tuple[int, int, int]
        Color del texto en formato RGB
    x : int
        Coordenada X donde se dibuja el texto
    y : int
        Coordenada Y donde se dibuja el texto
    align : str, optional
        Alineación del texto ("left", "center", "right"), por defecto "left
    ---------Returns---------
        _blit: Dibuja el texto en la superficie dada y devuelve la altura del texto renderizado
        _div: Dibuja una línea divisoria en la superficie dada y devuelve su altura 
        _fmt_secs: Formatea segundos como cadena MM:SS
        _draw_priority_badge: Dibuja una insignia de prioridad en la superficie dada y devuelve su altura
        _draw_footer: Dibuja el pie de página con controles y sistema en la superficie dada y devuelve la coordenada Y final
        _footer_with_autofit: Dibuja el pie de página adaptándose al espacio disponible y devuelve la coordenada Y final
        _draw_job_card: Dibuja una tarjeta de pedido en la superficie dada y devuelve la coordenada Y final
        _difficulty_label_and_color: Devuelve el texto y color para la dificultad de la IA
    """
    def _font(self, size):
        try:
            return pygame.font.Font(os.path.join("fonts", "RussoOne-Regular.ttf"), size)
        except Exception:
            return pygame.font.Font(None, size)

    def _blit(self, surf, text, font, col, x, y, align="left"):
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
        line = pygame.Surface((self.rect.width - 2*self.PAD, 1), pygame.SRCALPHA)
        line.fill((255, 255, 255, self.DIV_ALPHA))
        surf.blit(line, (self.rect.left + self.PAD, y))
        return 1

    # --------- helper para formatear segs ---------
    """
    Formatea segundos como cadena MM:SS
    ---------Parameters---------
    secs : float
        Segundos a formatear
    ---------Returns---------
        _fmt_secs: Devuelve una cadena formateada como MM:SS
    """
    def _fmt_secs(self, secs: float) -> str:
        secs = max(0, int(secs))
        m = secs // 60
        s = secs % 60
        return f"{m:02d}:{s:02d}"

    # --------- badge de prioridad en la card ---------
    """
    Dibuja una insignia de prioridad en la superficie dada y devuelve su altura
    ---------Parameters---------
    screen : pygame.Surface
        Superficie donde se dibuja la insignia
    x : int 
        Coordenada X donde se dibuja la insignia
    y : int 
        Coordenada Y donde se dibuja la insignia
    level : int
        Nivel de prioridad (0 bajo, 1 medio, 2 alto)
    ---------Returns---------   
        _draw_priority_badge: Dibuja la insignia y devuelve su altura
    """
    def _draw_priority_badge(self, screen, x, y, level: int):
        # colores suaves por nivel (0 bajo, 1 medio, 2 alto)
        if level >= 2:
            col = (255, 120, 120)   # alto
            txt = "PRIO 2"
        elif level == 1:
            col = (255, 200, 120)   # medio
            txt = "PRIO 1"
        else:
            col = (180, 220, 255)   # bajo
            txt = "PRIO 0"

        pad_h = 4
        pad_w = 8
        s = self.fs.render(txt, True, (0, 0, 0))
        w, h = s.get_width() + pad_w*2, s.get_height() + pad_h*2
        badge = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(badge, col + (180,), pygame.Rect(0, 0, w, h), border_radius=8)
        badge.blit(s, (pad_w, pad_h))
        screen.blit(badge, (x, y))
        return h

    """
    Dibuja el pie de página con controles y sistema en la superficie dada y devuelve la coordenada Y final
    ---------Parameters---------
    screen : pygame.Surface
        Superficie donde se dibuja el pie de página
    x : int    
        Coordenada X donde se dibuja el pie de página
    bottom : int    
        Coordenada Y inferior donde se dibuja el pie de página
    contextual : Optional[str]  
        Mensaje contextual opcional para mostrar en el pie de página
    f_body : pygame.font.Font   
        Fuente a utilizar para el cuerpo del pie de página
    gap_line : int
        Espacio entre líneas en el pie de página
    sec_gap : int   
        Espacio entre secciones en el pie de página
    ---------Returns---------   
        _draw_footer: Devuelve la coordenada Y final después de dibujar el pie de página
    """
    def _draw_footer(self, screen, x, bottom, contextual, f_body, gap_line, sec_gap):
        lh = f_body.get_linesize()
        y = bottom

        # Sistema
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

        # Mensaje contextual
        if contextual:
            y -= (self.f.get_linesize() + 10)
            color = self.hl if "ESPACIO" in contextual else self.ok
            self._blit(screen, contextual, self.f, color, x, y)

        return y

    """
    Dibuja el pie de página adaptándose al espacio disponible y devuelve la coordenada Y final
    ---------Parameters---------
    screen : pygame.Surface
        Superficie donde se dibuja el pie de página
    x : int    
        Coordenada X donde se dibuja el pie de página
    bottom : int    
        Coordenada Y inferior donde se dibuja el pie de página     
    top_limit : int
        Límite superior para evitar sobreposición con contenido principal
    contextual : Optional[str]  
        Mensaje contextual opcional para mostrar en el pie de página
    ---------Returns---------
        _footer_with_autofit: Devuelve la coordenada Y final después de dibujar el pie de página
    """
    def _footer_with_autofit(self, screen, x, bottom, top_limit, contextual):
        min_gap = 12
        top = self._draw_footer(
            screen, x, bottom, contextual, self.fs,
            self.FOOTER_GAP_LINE, self.FOOTER_SEC_GAP
        )
        if top < top_limit + min_gap:
            pygame.draw.rect(screen, self.bg,
                             pygame.Rect(self.rect.left, max(top, top_limit),
                                         self.rect.width, bottom - max(top, top_limit)))
            top = self._draw_footer(
                screen, x, bottom, contextual, self.fs_small,
                self.FOOTER_GAP_LINE_COMPACT, self.FOOTER_SEC_GAP_COMPACT
            )
        return top

    """
    Dibuja una tarjeta de pedido en la superficie dada y devuelve la coordenada Y final
    ---------Parameters---------
    screen : pygame.Surface
        Superficie donde se dibuja la tarjeta
    x : int
        Coordenada X donde se dibuja la tarjeta
    y : int
        Coordenada Y donde se dibuja la tarjeta
    w : int
        Ancho de la tarjeta
    job : Any
        Objeto de pedido con atributos id, payout, priority y método get_time_until_deadline
    current_game_time : Optional[float], optional
        Tiempo actual del juego para calcular el tiempo restante, por defecto None
    ---------Returns---------   
        _draw_job_card: Devuelve la coordenada Y final después de dibujar la tarjeta de pedido
    """
    def _draw_job_card(self, screen, x, y, w, job, current_game_time=None):
        card_h = self.CARD_H_MIN
        card_rect = pygame.Rect(x, y, w, card_h)
        s = pygame.Surface((w, card_h), pygame.SRCALPHA)
        s.fill(self.CARD_BG)
        screen.blit(s, (x, y))

        yy = y + self.CARD_PAD
        yy += self._blit(screen, "PEDIDO ACTUAL:", self.f, self.hl, x + self.CARD_PAD, yy)
        # Badge de prioridad alineado a la derecha
        try:
            prio = int(getattr(job, "priority", 0))
        except Exception:
            prio = 0
        self._draw_priority_badge(
            screen,
            x + w - self.CARD_PAD - 92,
            yy - self.f.get_linesize() + 2,
            prio
        )

        yy += self._blit(screen, f"ID: {job.id}", self.f, self.tx, x + self.CARD_PAD, yy)
        yy += self._blit(screen, f"Pago: ${job.payout:.1f}", self.f, self.tx, x + self.CARD_PAD, yy)

        # Tiempo restante
        if current_game_time is not None and hasattr(job, "get_time_until_deadline"):
            try:
                tl = float(job.get_time_until_deadline(current_game_time))
                tcol = self.warn if tl <= 0 else (self.hl if tl < 60 else self.tx)
                yy += self._blit(
                    screen,
                    f"Tiempo restante: {self._fmt_secs(tl)}",
                    self.f,
                    tcol,
                    x + self.CARD_PAD,
                    yy
                )
            except Exception:
                pass

        return card_rect.bottom

    # --------- Dificultad IA: label y color ---------
    """
    Devuelve (texto_label, color) para la dificultad de la IA.
    Soporta tanto Enum AIDifficulty como strings.
    ---------Returns---------
        _difficulty_label_and_color: Devuelve el texto y color para la dificultad de la IA
    """
    def _difficulty_label_and_color(self):
        """
        Devuelve (texto_label, color) para la dificultad de la IA.
        Soporta tanto Enum AIDifficulty como strings.
        """
        if self.ai_difficulty is None:
            return "Sin IA", self.subtx

        # Intentar extraer el nombre del Enum (AIDifficulty.EASY -> "EASY")
        name = getattr(self.ai_difficulty, "name", None)
        if not name:
            raw = str(self.ai_difficulty)
            # Por si viene como "AIDifficulty.EASY" o similar
            if "." in raw:
                name = raw.split(".")[-1]
            else:
                name = raw

        up = name.upper()

        if up in ("EASY", "FACIL", "FÁCIL"):
            return "FÁCIL", (120, 220, 120)
        elif up in ("MEDIUM", "MEDIO"):
            return "MEDIO", (240, 200, 120)
        elif up in ("HARD", "DIFICIL", "DIFÍCIL"):
            return "DIFÍCIL", (255, 140, 140)
        else:
            return name, self.subtx

    """
    Dibuja la HUD completa en la superficie dada con la información del courier, clima, tiempo, etc.
    ---------Parameters---------
    screen : pygame.Surface
        Superficie donde se dibuja la HUD
    courier : Any
        Objeto courier con atributos como x, y, stamina, income, reputation, packages_delivered
    weather_condition : str 
        Condición climática actual (no usada en este método)
    speed_multiplier : float    
        Multiplicador de velocidad actual (no usada en este método)
    remaining_time : float, optional    
        Tiempo restante en segundos, por defecto 0
    goal_income : float, optional
        Ingreso objetivo para el nivel, por defecto 0
    near_pickup : bool, optional    
        Indica si el courier está cerca de un punto de recogida, por defecto False
    near_dropoff : bool, optional
        Indica si el courier está cerca de un punto de entrega, por defecto False
    current_game_time : Optional[float], optional
        Tiempo actual del juego para calcular tiempos restantes, por defecto None
    ai_courier : Optional[Any], optional
        Objeto courier de la IA (CPU) para mostrar su estado, por defecto None
    ---------Returns---------   
        draw: Dibuja la HUD completa en la superficie dada
    """
    def draw(self, screen, courier, weather_condition, speed_multiplier,
             remaining_time=0, goal_income=0, near_pickup=False, near_dropoff=False,
             current_game_time=None, ai_courier=None):
        pygame.draw.rect(screen, self.bg, self.rect)
        pad = self.PAD
        x = self.rect.left + pad
        y = self.rect.top + pad
        content_w = self.rect.width - 2*pad

        # --- Título ---
        y += self._blit(
            screen,
            "COURIER QUEST",
            self.f_title,
            self.hl,
            self.rect.centerx,
            y,
            align="center"
        ) + self.SEC_GAP

        # Tiempo / Ingresos
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        tcol = self.warn if remaining_time < 60 else self.tx
        y += self._blit(screen, f"Tiempo: {minutes:02d}:{seconds:02d}", self.f, tcol, x, y) + self.VR_GAP
        icol = self.ok if courier.income >= goal_income else self.tx
        y += self._blit(
            screen,
            f"Ingresos: ${courier.income:.1f}/{int(goal_income)}",
            self.f,
            icol,
            x,
            y
        )
        y += self.SEC_GAP + self._div(screen, y)

        # --- Repartidor (jugador humano) ---
        y += self.SEC_GAP
        y += self._blit(screen, "--- Repartidor (Jugador) ---", self.fs, self.player_col, x, y)
        y += self.VR_GAP
        y += self._blit(screen, f"Posición: ({courier.x}, {courier.y})", self.fs, self.tx, x, y)
        delivered = getattr(courier, "packages_delivered", getattr(courier, "delivered_count", 0))
        y += self._blit(screen, f"Entregados: {delivered}", self.fs, self.tx, x, y)

        # Resistencia
        max_sta = max(1, int(getattr(courier, "max_stamina", 100)))
        sta_pct = max(0.0, min(1.0, courier.stamina / max_sta))
        bar_h = 20
        bar_rect = pygame.Rect(x, y + self.VR_GAP, content_w, bar_h)
        pygame.draw.rect(screen, (50, 50, 50), bar_rect)
        fill_rect = pygame.Rect(x, y + self.VR_GAP, int(content_w * sta_pct), bar_h)
        pygame.draw.rect(screen, self.warn if sta_pct < 0.3 else self.ok, fill_rect)
        y = bar_rect.bottom + 4
        y += self._blit(
            screen,
            f"Resistencia: {int(courier.stamina)}/{max_sta}",
            self.fs,
            self.tx,
            x + content_w//2,
            y,
            align="center"
        )
        y += self.SEC_GAP + self._div(screen, y)

        # Reputación
        y += self.SEC_GAP
        rep = int(getattr(courier, "reputation", 70))
        rcol = self.ok if rep >= 90 else self.warn if rep < 30 else self.tx
        y += self._blit(screen, f"Reputación: {rep}", self.f, rcol, x, y)
        y += self.SEC_GAP + self._div(screen, y)

        # --- IA (CPU) status (opcional) ---
        if ai_courier is not None:
            y += self.SEC_GAP
            # Encabezado IA con color propio
            y += self._blit(screen, "--- IA (CPU) ---", self.fs, self.ai_col, x, y)
            y += self.VR_GAP

            # Línea de dificultad IA
            diff_label, diff_col = self._difficulty_label_and_color()
            y += self._blit(
                screen,
                f"Dificultad IA: {diff_label}",
                self.fs,
                diff_col,
                x,
                y
            )
            y += self.VR_GAP

            # Posición de la IA
            y += self._blit(screen, f"Pos IA: ({ai_courier.x}, {ai_courier.y})", self.fs, self.tx, x, y)

            # Peso y pedidos activos de la IA
            inv_ai = getattr(ai_courier, "inventory", None)
            current_w_ai = getattr(inv_ai, "current_weight", 0.0) if inv_ai else 0.0
            max_w_ai = getattr(inv_ai, "max_weight", getattr(ai_courier, "max_weight_ia", 0))
            y += self._blit(
                screen,
                f"Peso IA: {current_w_ai:.1f}/{max_w_ai} kg",
                self.fs,
                self.tx,
                x,
                y
            )

            active_jobs_ai = 0
            if inv_ai is not None:
                if hasattr(inv_ai, "get_job_count"):
                    active_jobs_ai = inv_ai.get_job_count()
                elif hasattr(inv_ai, "jobs"):
                    active_jobs_ai = len(inv_ai.jobs)
            y += self._blit(
                screen,
                f"IA pedidos activos: {active_jobs_ai}",
                self.fs,
                self.tx,
                x,
                y
            )

            # Barra de resistencia de la IA
            max_sta_ai = max(1, int(getattr(ai_courier, "max_stamina", 100)))
            sta_pct_ai = max(0.0, min(1.0, ai_courier.stamina / max_sta_ai))
            bar_h_ai = 12
            bar_rect_ai = pygame.Rect(x, y + self.VR_GAP, content_w, bar_h_ai)
            pygame.draw.rect(screen, (50, 50, 50), bar_rect_ai)
            fill_rect_ai = pygame.Rect(x, y + self.VR_GAP, int(content_w * sta_pct_ai), bar_h_ai)
            pygame.draw.rect(screen, self.warn if sta_pct_ai < 0.3 else self.ok, fill_rect_ai)
            y = bar_rect_ai.bottom + 2
            y += self._blit(
                screen,
                f"IA Resistencia: {int(ai_courier.stamina)}/{max_sta_ai}",
                self.fs_small,
                self.tx,
                x + content_w // 2,
                y,
                align="center"
            )

            # Reputación IA
            y += self.SEC_GAP
            rep_ai = int(getattr(ai_courier, "reputation", 70))
            rcol_ai = self.ok if rep_ai >= 90 else self.warn if rep_ai < 30 else self.tx
            y += self._blit(screen, f"IA Reputación: {rep_ai}", self.fs, rcol_ai, x, y)

            # Comparación de ingresos Jugador vs IA
            y += self.VR_GAP
            player_inc = getattr(courier, "income", 0.0)
            ai_inc = getattr(ai_courier, "income", 0.0)
            comp_col = self.ok if player_inc >= ai_inc else self.warn
            y += self._blit(
                screen,
                f"Jugador: ${player_inc:.1f} vs IA: ${ai_inc:.1f}",
                self.fs,
                comp_col,
                x,
                y
            )

            y += self.SEC_GAP + self._div(screen, y)

        # Inventario (solo mensaje)
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

        # --- FOOTER y CARD ---
        bottom = self.rect.bottom - self.PAD
        contextual = None
        if near_pickup:
            contextual = "🟡 Presiona ESPACIO para recoger"
        elif near_dropoff:
            contextual = "🟢 Presiona E para entregar"

        est_top = self._draw_footer(
            screen,
            x,
            bottom,
            contextual,
            self.fs,
            self.FOOTER_GAP_LINE,
            self.FOOTER_SEC_GAP
        )
        pygame.draw.rect(
            screen,
            self.bg,
            pygame.Rect(self.rect.left, est_top, self.rect.width, bottom - est_top)
        )

        # Mostrar card del pedido actual si hay espacio
        if hasattr(courier, "has_jobs") and courier.has_jobs():
            job = courier.get_current_job()
            if job and (est_top - y) > self.CARD_H_MIN + self.SEC_GAP:
                y += self.SEC_GAP
                y = self._draw_job_card(screen, x, y, content_w, job, current_game_time=current_game_time)
                y += self.SEC_GAP
                y += self._div(screen, y)

        top_limit = max(y + 4, self.rect.top + self.PAD + 4)
        self._footer_with_autofit(screen, x, bottom, top_limit, contextual)
