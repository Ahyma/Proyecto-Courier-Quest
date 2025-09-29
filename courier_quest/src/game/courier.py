# src/game/courier.py
import pygame
from collections import deque

class Courier:
    def __init__(self, start_x, start_y, image=None, max_stamina=100, base_speed_cps=3.0):
        self.x, self.y = start_x, start_y
        self.image = image

        # Estado base
        self.max_stamina = max_stamina
        self.stamina = max_stamina
        self.reputation = 70
        self.money = 0.0

        # Movimiento
        self.v0 = base_speed_cps            # celdas/seg
        self._exhausted_lock = False        # si llegó a 0, queda bloqueado hasta 30

        # Inventario
        self.inventory = deque()            # lista de pedidos aceptados
        self.max_weight = 6                 # peso máximo transportable

    # ---- Inventario
    def total_weight(self):
        return sum(item.get("weight",0) for item in self.inventory)

    def can_accept(self, job):
        return self.total_weight() + job.get("weight",0) <= self.max_weight

    def accept_job(self, job):
        if self.can_accept(job):
            self.inventory.append(job)
            return True
        return False

    def rotate_forward(self):
        if self.inventory:
            self.inventory.rotate(-1)

    def rotate_backward(self):
        if self.inventory:
            self.inventory.rotate(1)

    # ---- Modificadores de velocidad (enunciado §8)
    def stamina_state_mult(self):
        if self.stamina <= 0:
            return 0.0
        if self.stamina < 30:
            return 0.8
        return 1.0

    def weight_mult(self):
        w = self.total_weight()
        return max(0.8, 1 - 0.03*max(0, w))

    def rep_mult(self):
        return 1.03 if self.reputation >= 90 else 1.0

    def speed(self, m_clima, m_surface):
        return self.v0 * m_clima * self.weight_mult() * self.rep_mult() * self.stamina_state_mult() * m_surface

    # ---- Consumo/recuperación de resistencia (enunciado §6)
    def _consume_per_cell(self, clima_label):
        base = 0.5
        extra = 0.0
        w = self.total_weight()
        if w > 3:
            extra += 0.2*(w-3)
        if clima_label in ("rain","wind"): extra += 0.1
        elif clima_label == "storm":       extra += 0.3
        elif clima_label == "heat":        extra += 0.2
        return base + extra

    def can_move(self):
        # Si alguna vez llegó a 0, no puede moverse hasta recuperar 30
        if self._exhausted_lock:
            return self.stamina >= 30
        return self.stamina > 0

    def step_to(self, nx, ny, clima_label, m_surface):
        if not self.can_move():
            return False
        self.x, self.y = nx, ny
        self.stamina -= self._consume_per_cell(clima_label)
        if self.stamina <= 0:
            self.stamina = 0
            self._exhausted_lock = True
        return True

    def rest(self, dt_seconds, boosted=False):
        gain = 10 if boosted else 5
        self.stamina = min(self.max_stamina, self.stamina + gain*dt_seconds)
        if self.stamina >= 30:
            self._exhausted_lock = False

    # ---- Dibujado
    def draw(self, screen, TILE):
        if self.image:
            screen.blit(self.image, (self.x*TILE, self.y*TILE))
        else:
            pygame.draw.circle(screen, (255,0,0),
                               (self.x*TILE+TILE//2, self.y*TILE+TILE//2),
                               TILE//2)
