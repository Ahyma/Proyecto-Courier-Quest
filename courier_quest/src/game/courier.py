import pygame
from .inventory import Inventory

class Courier:
    """
    Representa al repartidor/jugador en el juego.
    
    Responsabilidades:
    - Movimiento y navegación por el mundo
    - Gestión de stamina y estado físico
    - Manejo de inventario de pedidos
    - Cálculo de reputación y rachas
    - Interacción con el sistema de clima
    """
    
    def __init__(self, start_x, start_y, image,
                 max_stamina=100, base_speed=3.0, max_weight=10):
        """
        Inicializa el repartidor.
        
        Args:
            start_x, start_y: Posición inicial
            image: Imagen del repartidor
            max_stamina: Stamina máxima
            base_speed: Velocidad base de movimiento
            max_weight: Peso máximo que puede cargar
        """
        self.x = start_x  # Posición X en tiles
        self.y = start_y  # Posición Y en tiles
        self.image = image  # Sprite del repartidor

        # Atributos de estado
        self.base_speed = base_speed
        self.stamina = max_stamina
        self.max_stamina = max_stamina
        self.income = 0.0  # Dinero ganado
        self.reputation = 70  # Reputación inicial
        self.max_weight = max_weight  # Capacidad de carga

        # Sistema de inventario
        self.inventory = Inventory(max_weight)
        self.packages_delivered = 0  # Contador de entregas exitosas

        # Racha de entregas sin penalización
        self._clean_streak = 0
        
        # NUEVO: Sistema de exhaustión y recuperación
        self.is_exhausted = False  # Si está demasiado cansado para moverse
        self.recovery_rate_normal = 5.0  # +5 stamina por segundo normal
        self.recovery_rate_resting = 10.0  # +10 stamina por segundo en puntos de descanso
        self.exhaustion_threshold = 0.3 * max_stamina  # 30% para recuperarse de exhaustión

    @property
    def current_weight(self):
        """Peso actual que está cargando (suma de todos los pedidos)."""
        return self.inventory.current_weight

    @property
    def stamina_state(self):
        """Estado actual de stamina para mostrar en HUD."""
        if self.is_exhausted:
            return "exhausto"
        elif self.stamina <= 30:
            return "cansado"
        else:
            return "normal"

    def move(self, dx, dy, stamina_cost_modifier=1.0, surface_weight=1.0, climate_mult=1.0):
        """
        Mueve al repartidor aplicando todos los modificadores.
        
        Args:
            dx, dy: Dirección del movimiento
            stamina_cost_modifier: Multiplicador de costo por clima
            surface_weight: Multiplicador por tipo de superficie
            climate_mult: Multiplicador por condición climática
        """
        # NUEVO: Verificar si está exhausto (no puede moverse)
        if self.is_exhausted:
            print("⚠️  Demasiado exhausto para moverse. Descansa para recuperarte.")
            return
        
        # Cálculo de modificadores de velocidad
        Mpeso = max(0.8, 1 - 0.03 * self.current_weight)  # Penalización por peso
        Mrep = 1.03 if self.reputation >= 90 else 1.0  # Bono por reputación alta

        # Modificador por estado de stamina
        if self.stamina <= 0:
            Mresistencia = 0.0  # Sin stamina = no movimiento
            # NUEVO: Marcar como exhausto si se queda sin stamina
            self.is_exhausted = True
            print("💤 ¡Exhausto! Descansa para recuperarte hasta 30% de stamina.")
        elif self.stamina <= 30:
            Mresistencia = 0.8  # Stamina baja = 80% de velocidad
        else:
            Mresistencia = 1.0  # Stamina normal = velocidad completa

        # Cálculo de velocidad final con todos los modificadores
        final_speed = (self.base_speed * climate_mult * Mpeso * Mrep * Mresistencia * surface_weight)
        
        # Si no hay stamina, no moverse
        if Mresistencia == 0:
            return

        # Aplicar movimiento
        self.x += dx
        self.y += dy

        # Calcular costo de stamina
        base_stamina_cost = 0.5
        extra_weight_penalty = 0.2 * max(0, self.current_weight - 3)  # Penalización por exceso de peso
        total_cost = (base_stamina_cost + extra_weight_penalty) * stamina_cost_modifier
        self.stamina = max(0, self.stamina - total_cost)
        
        # NUEVO: Actualizar estado exhausto si se queda sin stamina
        if self.stamina <= 0:
            self.is_exhausted = True

    def recover_stamina(self, delta_time, is_resting_spot=False):
        """
        Recupera stamina con el tiempo.
        
        Args:
            delta_time: Tiempo transcurrido en segundos
            is_resting_spot: Si está en un punto de descanso especial
        """
        # Si ya tiene stamina máxima, no hacer nada
        if self.stamina >= self.max_stamina:
            return
        
        # Determinar tasa de recuperación según ubicación
        recovery_rate = self.recovery_rate_resting if is_resting_spot else self.recovery_rate_normal
        
        # Aplicar recuperación
        new_stamina = self.stamina + (recovery_rate * delta_time)
        
        # Manejo especial si estaba exhausto
        if self.is_exhausted:
            # Solo recuperar hasta el umbral de 30% cuando está exhausto
            if new_stamina >= self.exhaustion_threshold:
                self.is_exhausted = False
                print("✅ ¡Recuperado! Ya puedes moverte otra vez.")
            new_stamina = min(new_stamina, self.exhaustion_threshold)
        else:
            # Recuperación normal (hasta máximo)
            new_stamina = min(new_stamina, self.max_stamina)
        
        self.stamina = new_stamina

    # ---------- Inventario ----------
    def can_pickup_job(self, job):
        """Verifica si puede recoger un pedido (capacidad disponible)."""
        return self.inventory.can_add_job(job)

    def pickup_job(self, job):
        """Intenta recoger un pedido y agregarlo al inventario."""
        return self.inventory.add_job(job)

    def deliver_current_job(self):
        """
        Entrega el pedido actualmente seleccionado.
        
        Returns:
            El job entregado o None si no hay pedido
        """
        delivered_job = self.inventory.remove_current_job()
        if delivered_job:
            self.packages_delivered += 1  # Incrementar contador
        return delivered_job

    def get_current_job(self):
        """Obtiene el pedido actualmente seleccionado en el inventario."""
        return self.inventory.current_job

    def next_job(self):
        """Selecciona el siguiente pedido en el inventario."""
        return self.inventory.next_job()

    def previous_job(self):
        """Selecciona el pedido anterior en el inventario."""
        return self.inventory.previous_job()

    def has_jobs(self):
        """Verifica si tiene pedidos en el inventario."""
        return not self.inventory.is_empty()

    def get_job_count(self):
        """Obtiene la cantidad de pedidos en el inventario."""
        return self.inventory.get_job_count()

    # ---------- Reputación / Racha ----------
    def update_reputation(self, delta: int) -> bool:
        """
        Actualiza la reputación y gestiona rachas.
        
        Args:
            delta: Cambio a aplicar a la reputación
            
        Returns:
            True si la reputación cayó por debajo de 20 (derrota)
        """
        # Gestionar racha de entregas limpias
        if delta >= 0:
            self._clean_streak += 1  # Incrementar racha por entrega positiva
        else:
            self._clean_streak = 0  # Resetear racha por penalización

        # Aplicar cambio base a reputación (limitado entre 0-100)
        self.reputation = max(0, min(100, self.reputation + delta))

        # Bono por racha de 3 entregas sin penalización
        if self._clean_streak >= 3:
            self.reputation = min(100, self.reputation + 2)
            self._clean_streak = 0  # Resetear racha después del bono
            print("🔥 Racha de 3 entregas sin penalización: reputación +2")

        # Verificar condición de derrota
        return self.reputation < 20

    def get_reputation_multiplier(self):
        """
        Obtiene multiplicador de pago por reputación alta.
        
        Returns:
            1.05 si reputación ≥90, 1.0 si no
        """
        return 1.05 if self.reputation >= 90 else 1.0

    # ---------- Save/Load ----------
    def get_save_state(self):
        """
        Obtiene el estado actual para guardar partida.
        
        Returns:
            Diccionario con todos los datos importantes
        """
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
        """
        Carga el estado desde datos guardados.
        
        Args:
            state: Diccionario con estado guardado
        """
        self.x = state.get("x", 0)
        self.y = state.get("y", 0)
        self.stamina = state.get("stamina", self.max_stamina)
        self.income = state.get("income", 0.0)
        self.reputation = state.get("reputation", 70)
        self.packages_delivered = state.get("packages_delivered", 0)
        self._clean_streak = state.get("_clean_streak", 0)

    # ---------- Render ----------
    def draw(self, screen, TILE_SIZE):
        """Dibuja al repartidor en la pantalla."""
        if self.image:
            screen.blit(self.image, (self.x * TILE_SIZE, self.y * TILE_SIZE))

    def get_status_info(self):
        """
        Obtiene información de estado para debugging/HUD.
        
        Returns:
            Diccionario con información del estado actual
        """
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
        """Representación en string para debugging."""
        return (f"Courier(pos=({self.x},{self.y}), stamina={self.stamina}, "
                f"income=${self.income}, rep={self.reputation}, "
                f"jobs={self.get_job_count()}/{self.max_weight}kg)")