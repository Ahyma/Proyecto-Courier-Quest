import pygame
from datetime import datetime, timedelta

class Job:
    """
    Representa un pedido individual en el juego.
    """
    def __init__(self, job_data, game_start_time):
        self.id = job_data.get('id', 'UNKNOWN')
        self.pickup_pos = tuple(job_data.get('pickup', [0, 0]))
        self.dropoff_pos = tuple(job_data.get('dropoff', [0, 0]))
        self.payout = float(job_data.get('payout', 0))
        self.weight = job_data.get('weight', 0)
        self.priority = job_data.get('priority', 0)
        self.release_time = float(job_data.get('release_time', 0))

        # Deadline absoluto (datetime)
        deadline_str = job_data.get('deadline', '')
        try:
            # Acepta "...Z" y sin zona
            self.deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
        except Exception:
            self.deadline = None

        # Estado inicial: si release_time > 0, arranca 'pending'; si no, 'available'
        self.state = "pending" if self.release_time > 0 else "available"

        self.pickup_time: float | None = None   # segundos desde inicio de partida
        self.delivery_time: float | None = None # segundos desde inicio de partida

        self.game_start_time = game_start_time

    # ---------- Helpers de tiempo ----------
    def _now_dt(self, current_game_time: float) -> datetime:
        return self.game_start_time + timedelta(seconds=current_game_time)

    def time_until_deadline(self, current_game_time: float) -> float:
        """Segundos restantes hasta el deadline (>=0). Si no hay deadline, inf."""
        if not self.deadline:
            return float('inf')
        left = (self.deadline - self._now_dt(current_game_time)).total_seconds()
        return max(0.0, left)

    # ---------- Ciclo de vida ----------
    def is_available(self, current_game_time: float) -> bool:
        """Disponible si pasó su release_time y no está tomada/entregada/cancelada/expirada."""
        if self.state in ("delivered", "cancelled", "expired", "picked_up"):
            return False
        return current_game_time >= self.release_time

    def pickup(self, current_game_time: float) -> bool:
        """Marca el pedido como recogido."""
        if self.state in ("available",) or (self.state == "pending" and self.is_available(current_game_time)):
            self.state = "picked_up"
            self.pickup_time = current_game_time
            return True
        return False

    def deliver(self, current_game_time: float) -> bool:
        """Marca el pedido como entregado (si no expiró)."""
        if self.state == "picked_up":
            if self.is_expired(current_game_time):
                self.state = "expired"
                return False
            self.state = "delivered"
            self.delivery_time = current_game_time
            return True
        return False

    def cancel(self) -> bool:
        if self.state in ("available", "pending", "picked_up"):
            self.state = "cancelled"
            return True
        return False

    def is_expired(self, current_game_time: float) -> bool:
        """
        Expira si hay deadline y ya pasó, mientras no esté entregado/cancelado.
        (Se chequea también cuando está en 'picked_up'.)
        """
        if self.state in ("delivered", "cancelled", "expired"):
            return self.state == "expired"
        if not self.deadline:
            return False
        return self._now_dt(current_game_time) > self.deadline

    def is_close_to_pickup(self, courier_pos, distance=2):
        cx, cy = courier_pos
        px, py = self.pickup_pos
        return (abs(cx - px) <= distance and abs(cy - py) <= distance)

    def is_at_pickup(self, courier_pos):
        cx, cy = courier_pos
        px, py = self.pickup_pos
        return (abs(cx - px) + abs(cy - py)) <= 1

    def is_at_dropoff(self, courier_pos):
        cx, cy = courier_pos
        dx, dy = self.dropoff_pos
        return (abs(cx - dx) + abs(cy - dy)) <= 1

    # ---------- Reputación por puntualidad ----------
    def calculate_reputation_change(self) -> int:
        """
        Usa la tabla:
          +5  entrega temprana (≥20% antes del tiempo previsto)
          +3  entrega a tiempo
          -2  ≤30 s tarde
          -5  31–120 s tarde
          -10 >120 s tarde
        Donde el tiempo previsto = (deadline - pickup_time).
        Si no hubo pickup o deadline, no modifica.
        """
        if self.state != "delivered" or self.delivery_time is None or self.pickup_time is None or not self.deadline:
            return 0

        # Duración real (seg) desde pickup hasta entrega
        real_duration = self.delivery_time - self.pickup_time

        # Tiempo previsto (seg) desde pickup hasta deadline
        planned_duration = (self.deadline - (self.game_start_time + timedelta(seconds=self.pickup_time))).total_seconds()
        if planned_duration <= 0:
            # Si el planned es inválido, no aplicar delta
            return 0

        # Lateness: negativo si llegó antes, positivo si llegó tarde
        lateness = real_duration - planned_duration

        if lateness <= -0.20 * planned_duration:
            return 5  # ≥20% antes
        if lateness <= 0:
            return 3  # a tiempo (o levemente antes sin llegar al 20%)
        if lateness <= 30:
            return -2
        if lateness <= 120:
            return -5
        return -10

    # ---------- Marcadores (visual) ----------
    def draw_markers(self, screen, TILE_SIZE, courier_pos):
        if self.state == "picked_up":
            rx, ry = self.dropoff_pos
            pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(rx * TILE_SIZE, ry * TILE_SIZE, TILE_SIZE, TILE_SIZE), 2)
        elif (self.state in ("available", "pending") and self.is_close_to_pickup(courier_pos)):
            px, py = self.pickup_pos
            pygame.draw.rect(screen, (255, 255, 0), pygame.Rect(px * TILE_SIZE, py * TILE_SIZE, TILE_SIZE, TILE_SIZE), 2)

    def __str__(self):
        return f"Job {self.id} - {self.state} - ${self.payout} - {self.weight}kg"
