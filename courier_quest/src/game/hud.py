import pygame
import os

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

    def __init__(self, rect_area, screen_height, tile_size):
        self.rect = rect_area
        self.screen_height = screen_height
        self.tile_size = tile_size

        # Colores
        self.bg = (20, 20, 20)
        self.tx = (255, 255, 255)
        self.hl = (255, 215, 0)
        self.warn = (255, 100, 100)
        self.ok = (100, 255, 100)
        self.hint = (200, 200, 255)
        self.sortc = (180, 230, 180)
        self.subtx = (180, 180, 180)

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
            "Ctrl+Z: Deshacer"  # NUEVO: agregado deshacer
        ]

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

    def _fmt_secs(self, secs: float) -> str:
        secs = max(0, int(secs))
        m = secs // 60
        s = secs % 60
        return f"{m:02d}:{s:02d}"

    def _draw_priority_badge(self, screen, x, y, level: int):
        if level >= 2:
            col = (255, 120, 120)
            txt = "PRIO 2"
        elif level == 1:
            col = (255, 200, 120)
            txt = "PRIO 1"
        else:
            col = (180, 220, 255)
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

    def _draw_job_card(self, screen, x, y, w, job, current_game_time=None):
        card_h = self.CARD_H_MIN
        card_rect = pygame.Rect(x, y, w, card_h)
        s = pygame.Surface((w, card_h), pygame.SRCALPHA)
        s.fill(self.CARD_BG)
        screen.blit(s, (x, y))

        yy = y + self.CARD_PAD
        yy += self._blit(screen, "PEDIDO ACTUAL:", self.f, self.hl, x + self.CARD_PAD, yy)
        try:
            prio = int(getattr(job, "priority", 0))
        except Exception:
            prio = 0
        self._draw_priority_badge(screen, x + w - self.CARD_PAD - 92, yy - self.f.get_linesize() + 2, prio)

        yy += self._blit(screen, f"ID: {job.id}", self.f, self.tx, x + self.CARD_PAD, yy)
        yy += self._blit(screen, f"Pago: ${job.payout:.1f}", self.f, self.tx, x + self.CARD_PAD, yy)

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
             current_game_time=None, current_surface_weight=1.0):  # NUEVO: parámetro agregado

        pygame.draw.rect(screen, self.bg, self.rect)
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
        tcol = self.warn if remaining_time < 60 else self.tx
        y += self._blit(screen, f"Tiempo: {minutes:02d}:{seconds:02d}", self.f, tcol, x, y) + self.VR_GAP
        icol = self.ok if courier.income >= goal_income else self.tx
        y += self._blit(screen, f"Ingresos: ${courier.income:.1f}/{int(goal_income)}", self.f, icol, x, y)
        y += self.SEC_GAP + self._div(screen, y)

        # --- Repartidor ---
        y += self.SEC_GAP
        y += self._blit(screen, "--- Repartidor ---", self.fs, self.tx, x, y)
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
        
        # NUEVO: Mostrar efecto de superficie
        y += self._blit(screen, f"Superficie: {int(current_surface_weight*100)}%", self.fs, self.tx, x, y)

        # --- FOOTER y CARD ---
        bottom = self.rect.bottom - self.PAD
        contextual = None
        if near_pickup:
            contextual = "🟡 Presiona ESPACIO para recoger"
        elif near_dropoff:
            contextual = "🟢 Presiona E para entregar"

        est_top = self._draw_footer(screen, x, bottom, contextual, self.fs,
                                    self.FOOTER_GAP_LINE, self.FOOTER_SEC_GAP)
        pygame.draw.rect(screen, self.bg,
                         pygame.Rect(self.rect.left, est_top, self.rect.width, bottom - est_top))

        if hasattr(courier, "has_jobs") and courier.has_jobs():
            job = courier.get_current_job()
            if job and (est_top - y) > self.CARD_H_MIN + self.SEC_GAP:
                y += self.SEC_GAP
                y = self._draw_job_card(screen, x, y, content_w, job, current_game_time=current_game_time)
                y += self.SEC_GAP
                y += self._div(screen, y)

        top_limit = max(y + 4, self.rect.top + self.PAD + 4)
        self._footer_with_autofit(screen, x, bottom, top_limit, contextual)