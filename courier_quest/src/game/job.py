import pygame
from datetime import datetime, timedelta

class Job:
    """
    Representa un pedido individual en el juego.
    
    Maneja el ciclo de vida completo de un pedido:
    - Disponibilidad por tiempo de liberación
    - Recogida por el repartidor
    - Entrega en destino
    - Expiración por deadline
    - Cálculo de reputación por puntualidad
    """
    
    def __init__(self, job_data, game_start_time):
        """
        Inicializa un pedido con datos específicos.
        
        Args:
            job_data: Diccionario con datos del pedido
            game_start_time: Hora de inicio del juego para cálculos de tiempo
        """
        self.id = job_data.get('id', 'UNKNOWN')  # Identificador único
        self.pickup_pos = tuple(job_data.get('pickup', [0, 0]))  # Posición de recogida
        self.dropoff_pos = tuple(job_data.get('dropoff', [0, 0]))  # Posición de entrega
        self.payout = float(job_data.get('payout', 0))  # Pago por entrega
        self.weight = job_data.get('weight', 0)  # Peso del paquete
        self.priority = job_data.get('priority', 0)  # Prioridad (0=baja, 2=alta)
        self.release_time = float(job_data.get('release_time', 0))  # Tiempo hasta disponibilidad

        # Deadline absoluto (datetime)
        deadline_str = job_data.get('deadline', '')
        try:
            # Convertir string a datetime, manejar formato con/sin zona horaria
            self.deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
        except Exception:
            self.deadline = None  # Sin deadline

        # Estado inicial del pedido
        self.state = "pending" if self.release_time > 0 else "available"

        # Tiempos de recogida y entrega (segundos desde inicio de partida)
        self.pickup_time: float | None = None
        self.delivery_time: float | None = None

        self.game_start_time = game_start_time  # Referencia temporal del juego

    # ---------- Helpers de tiempo ----------
    def _now_dt(self, current_game_time: float) -> datetime:
        """Convierte tiempo de juego a datetime."""
        return self.game_start_time + timedelta(seconds=current_game_time)

    def time_until_deadline(self, current_game_time: float) -> float:
        """
        Calcula segundos restantes hasta el deadline.
        
        Returns:
            Segundos restantes o infinito si no hay deadline
        """
        if not self.deadline:
            return float('inf')  # Sin deadline
        left = (self.deadline - self._now_dt(current_game_time)).total_seconds()
        return max(0.0, left)  # No negativo

    # ---------- Ciclo de vida ----------
    def is_available(self, current_game_time: float) -> bool:
        """
        Verifica si el pedido está disponible para recoger.
        
        Returns:
            True si está disponible y no está en estado final
        """
        if self.state in ("delivered", "cancelled", "expired", "picked_up"):
            return False  # Estados finales
        return current_game_time >= self.release_time  # Pasó tiempo de liberación

    # Ya no requiere tiempo, solo devuelve posicion de pickup
    def pickup(self):
        return self.pickup_pos

    def deliver(self, current_game_time: float) -> bool:
        """
        Marca el pedido como entregado.
        
        Returns:
            True si se pudo entregar exitosamente
        """
        if self.state == "picked_up":
            if self.is_expired(current_game_time):
                self.state = "expired"  # Expiró antes de entregar
                return False
            self.state = "delivered"
            self.delivery_time = current_game_time
            return True
        return False

    def cancel(self) -> bool:
        """Cancela el pedido si está en estado cancelable."""
        if self.state in ("available", "pending", "picked_up"):
            self.state = "cancelled"
            return True
        return False

    def is_expired(self, current_game_time: float) -> bool:
        """
        Verifica si el pedido ha expirado por deadline.
        
        Returns:
            True si expiró y no está en estado final
        """
        if self.state in ("delivered", "cancelled", "expired"):
            return self.state == "expired"  # Ya está expirado
        if not self.deadline:
            return False  # Sin deadline, no expira
        return self._now_dt(current_game_time) > self.deadline  # Pasó deadline

    def is_close_to_pickup(self, courier_pos, distance=2):
        """Verifica si el repartidor está cerca del punto de recogida."""
        cx, cy = courier_pos
        px, py = self.pickup_pos
        return (abs(cx - px) <= distance and abs(cy - py) <= distance)

    def is_at_pickup(self, courier_pos):
        """Verifica si el repartidor está en el punto de recogida (adyacente)."""
        cx, cy = courier_pos
        px, py = self.pickup_pos
        return (abs(cx - px) + abs(cy - py)) <= 1  # Distancia Manhattan <= 1

    def is_at_dropoff(self, courier_pos):
        """Verifica si el repartidor está en el punto de entrega (adyacente)."""
        cx, cy = courier_pos
        dx, dy = self.dropoff_pos
        return (abs(cx - dx) + abs(cy - dy)) <= 1  # Distancia Manhattan <= 1

    # ---------- Reputación por puntualidad ----------
    def calculate_reputation_change(self) -> int:
        """
        Calcula cambio de reputación basado en puntualidad.
        
        Tabla de puntuación:
          +5  entrega temprana (≥20% antes del tiempo previsto)
          +3  entrega a tiempo
          -2  ≤30 s tarde
          -5  31–120 s tarde
          -10 >120 s tarde
          
        Returns:
            Cambio de reputación (-10 a +5)
        """
        if self.state != "delivered" or self.delivery_time is None or self.pickup_time is None or not self.deadline:
            return 0  # No aplica si falta información

        # Duración real desde recogida hasta entrega
        real_duration = self.delivery_time - self.pickup_time

        # Tiempo previsto desde recogida hasta deadline
        planned_duration = (self.deadline - (self.game_start_time + timedelta(seconds=self.pickup_time))).total_seconds()
        if planned_duration <= 0:
            return 0  # Planned inválido

        # Tardanza: negativo si llegó antes, positivo si llegó tarde
        lateness = real_duration - planned_duration

        # Aplicar tabla de puntuación
        if lateness <= -0.20 * planned_duration:
            return 5  # ≥20% antes
        if lateness <= 0:
            return 3  # a tiempo
        if lateness <= 30:
            return -2
        if lateness <= 120:
            return -5
        return -10

    # ---------- Marcadores (visual) ----------
    def draw_markers(self, screen, TILE_SIZE, courier_pos):
        """Dibuja marcadores visuales para el pedido."""
        if self.state == "picked_up":
            # Destino verde para pedidos recogidos
            rx, ry = self.dropoff_pos
            pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(rx * TILE_SIZE, ry * TILE_SIZE, TILE_SIZE, TILE_SIZE), 2)
        elif (self.state in ("available", "pending") and self.is_close_to_pickup(courier_pos)):
            # Origen amarillo para pedidos disponibles cercanos
            px, py = self.pickup_pos
            pygame.draw.rect(screen, (255, 255, 0), pygame.Rect(px * TILE_SIZE, py * TILE_SIZE, TILE_SIZE, TILE_SIZE), 2)

    def __str__(self):
        """Representación en string para debugging."""
        return f"Job {self.id} - {self.state} - ${self.payout} - {self.weight}kg"