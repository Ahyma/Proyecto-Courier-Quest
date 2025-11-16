import pygame
from .inventory import Inventory

class Courier:
    def __init__(self, start_x, start_y, image,
                 max_stamina=100, base_speed=3.0, max_weight=10):
        self.x = start_x
        self.y = start_y
        self.image = image

        self.base_speed = base_speed
        self.stamina = max_stamina
        self.max_stamina = max_stamina
        self.income = 0.0
        self.reputation = 70
        self.max_weight = max_weight

        self.inventory = Inventory(max_weight)
        self.packages_delivered = 0

        # Racha de entregas sin penalización
        self._clean_streak = 0  # cuenta entregas con delta de reputación >= 0

    @property
    def current_weight(self):
        return self.inventory.current_weight

    @property
    def stamina_state(self):
        if self.stamina <= 0:
            return "exhausto"
        elif self.stamina <= 30:
            return "cansado"
        else:
            return "normal"

    """
    Mueve el courier un paso en la cuadrícula considerando varios modificadores (clima, peso, reputación, resistencia)

    ---------Parameters---------
    dx : int
        Desplazamiento en x (puede ser negativo)
    dy : int
        Desplazamiento en y (puede ser negativo)

    stamina_cost_modifier : float
        Modificador para el coste de stamina 
    
    surface_weight : float
        Peso del terreno actual (afecta a la velocidad)

    climate_mult : float
        Multiplicador de velocidad según el clima actual

    game_world :
        Objeto que expone is_walkable(x: int, y: int) -> bool para
        verificar si la nueva posición es transitable.
        Si se proporciona, se usa game_world.is_walkable para evitar que el courier pase encima de edificios o de obstáculos

    ---------Returns---------
        True si el movimiento fue exitoso, False si no (por ejemplo, terreno no transitable)
        True si se aplicó el movimiento (x, y actualizados)
        False si el movimiento fue bloqueado (por ejemplo, tile no transitable)
    """
    def move(self, dx, dy, stamina_cost_modifier=1.0, surface_weight=1.0, climate_mult=1.0, game_world=None):
        Mpeso = max(0.8, 1 - 0.03 * self.current_weight)
        Mrep = 1.03 if self.reputation >= 90 else 1.0

        if self.stamina <= 0:
            Mresistencia = 0.0
        elif self.stamina <= 30:
            Mresistencia = 0.8
        else:
            Mresistencia = 1.0

        final_speed = (self.base_speed * climate_mult * Mpeso * Mrep * Mresistencia * surface_weight)
        if Mresistencia == 0:
            return

        # Comprobar transitabilidad si se provee world
        new_x = self.x + dx
        new_y = self.y + dy
        if game_world is not None:
            try:
                if not game_world.is_walkable(new_x, new_y):
                    return False
            except Exception:
                # Si game_world no expone is_walkable correctamente, evitar crash y permitir movimiento
                pass

        # Aplicar movimiento
        self.x = new_x
        self.y = new_y

        base_stamina_cost = 0.5
        extra_weight_penalty = 0.2 * max(0, self.current_weight - 3)
        total_cost = (base_stamina_cost + extra_weight_penalty) * stamina_cost_modifier
        self.stamina = max(0, self.stamina - total_cost)
        return True

    # ---------- Inventario ----------
    def can_pickup_job(self, job):
        return self.inventory.can_add_job(job)

    def pickup_job(self, job):
        return self.inventory.add_job(job)

    def deliver_current_job(self):
        delivered_job = self.inventory.remove_current_job()
        if delivered_job:
            self.packages_delivered += 1
        return delivered_job

    def get_current_job(self):
        return self.inventory.current_job

    def next_job(self):
        return self.inventory.next_job()

    def previous_job(self):
        return self.inventory.previous_job()

    def has_jobs(self):
        return not self.inventory.is_empty()

    def get_job_count(self):
        return self.inventory.get_job_count()

    # ---------- Reputación / Racha ----------
    def update_reputation(self, delta: int) -> bool:
        """
        Aplica delta y gestiona racha:
          - si delta >= 0 → incrementa racha; si llega a 3 → bono +2 y resetea.
          - si delta < 0 → resetea racha.
        Devuelve True si la reputación cae por debajo de 20 (derrota).
        """
        if delta >= 0:
            self._clean_streak += 1
        else:
            self._clean_streak = 0

        # Aplica delta base
        self.reputation = max(0, min(100, self.reputation + delta))

        # Bono por racha de 3 entregas sin penalización
        if self._clean_streak >= 3:
            self.reputation = min(100, self.reputation + 2)
            self._clean_streak = 0
            print("🔥 Racha de 3 entregas sin penalización: reputación +2")

        return self.reputation < 20

    def get_reputation_multiplier(self):
        return 1.05 if self.reputation >= 90 else 1.0

    # ---------- Save/Load ----------
    def get_save_state(self):
        return {
            "x": self.x,
            "y": self.y,
            "stamina": self.stamina,
            "income": self.income,
            "reputation": self.reputation,
            "packages_delivered": self.packages_delivered,
            "current_weight": self.current_weight,
            "_clean_streak": self._clean_streak,
        }

    def load_state(self, state):
        self.x = state.get("x", 0)
        self.y = state.get("y", 0)
        self.stamina = state.get("stamina", self.max_stamina)
        self.income = state.get("income", 0.0)
        self.reputation = state.get("reputation", 70)
        self.packages_delivered = state.get("packages_delivered", 0)
        self._clean_streak = state.get("_clean_streak", 0)

    # ---------- Render ----------
    def draw(self, screen, TILE_SIZE):
        if self.image:
            screen.blit(self.image, (self.x * TILE_SIZE, self.y * TILE_SIZE))

    def get_status_info(self):
        current_job = self.get_current_job()
        job_info = current_job.id if current_job else "Ninguno"
        return {
            "position": (self.x, self.y),
            "stamina": f"{self.stamina}/{self.max_stamina}",
            "income": self.income,
            "reputation": self.reputation,
            "weight": f"{self.current_weight}/{self.max_weight}kg",
            "current_job": job_info,
            "total_jobs": self.get_job_count(),
            "delivered": self.packages_delivered,
            "state": self.stamina_state
        }

    def __str__(self):
        return (f"Courier(pos=({self.x},{self.y}), stamina={self.stamina}, "
                f"income=${self.income}, rep={self.reputation}, "
                f"jobs={self.get_job_count()}/{self.max_weight}kg)")
