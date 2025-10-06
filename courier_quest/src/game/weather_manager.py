import random

class WeatherManager:
    """
    Sistema de gestión del clima usando cadenas de Markov para transiciones.
    
    Características:
    - Transiciones suaves entre estados climáticos
    - Ráfagas de clima que duran 45-60 segundos
    - Intensidad variable (0-1) que afecta efectos
    - Multiplicadores de velocidad y consumo de resistencia
    """
    
    def __init__(self, weather_data):
        """
        Inicializa el gestor de clima.
        
        Args:
            weather_data: Datos de configuración del clima
        """
        self.data = weather_data.get("data", {})
        self.transition_matrix = self.data.get("transition", {}) or {}

        # Ajustar probabilidades para hacer el clima más dinámico
        if "clear" in self.transition_matrix:
            self.transition_matrix["clear"] = {
                "clear": 0.5,      # 50% chance de mantenerse despejado
                "clouds": 0.4,     # 40% chance de nubes
                "rain_light": 0.1  # 10% chance de lluvia ligera
            }

        # Estado inicial del clima
        initial = self.data.get("initial", {})
        self.current_condition = initial.get("condition", "clear")
        self.current_intensity = float(initial.get("intensity", 0.0))  # 0–1
        self.next_condition = None
        self.transitioning = False  # Indica si está en transición

        # Tabla de multiplicadores base por condición climática
        self.multipliers = {
            "clear":      {"speed": 1.00, "stamina_cost": 0.00},  # Sin efectos
            "clouds":     {"speed": 0.98, "stamina_cost": 0.00},  # Ligera reducción
            "rain_light": {"speed": 0.90, "stamina_cost": 0.10},  # Reducción moderada
            "rain":       {"speed": 0.85, "stamina_cost": 0.10},  # Reducción significativa
            "storm":      {"speed": 0.75, "stamina_cost": 0.30},  # Fuerte reducción
            "fog":        {"speed": 0.88, "stamina_cost": 0.00},  # Reducción por visibilidad
            "wind":       {"speed": 0.92, "stamina_cost": 0.05},  # Ligera reducción
            "heat":       {"speed": 0.90, "stamina_cost": 0.20},  # Reducción por calor
            "cold":       {"speed": 0.92, "stamina_cost": 0.00},  # Ligera reducción
        }

        # Configuración de temporizadores
        self._reset_burst_timer()             # 45–60 s entre cambios
        self.transition_duration = 4.0        # Duración de transición (se randomiza)
        self.time_since_last_change = 0.0     # Tiempo desde último cambio
        self.transition_timer = 0.0           # Tiempo en transición actual

        # Variables para interpolación suave entre estados
        self.initial_speed_mult = 1.0
        self.final_speed_mult = 1.0
        self.initial_stamina_cost = 0.0
        self.final_stamina_cost = 0.0
        self.initial_intensity = self.current_intensity
        self.final_intensity = self.current_intensity

    # --------------------------
    # Utilidades
    # --------------------------
    @staticmethod
    def _clamp(x, lo, hi):
        """Asegura que un valor esté dentro de un rango."""
        return max(lo, min(hi, x))

    def _reset_burst_timer(self):
        """Reinicia el temporizador de ráfagas con valor aleatorio."""
        self.burst_timer = random.uniform(45.0, 60.0)

    def _pick_transition_duration(self):
        """Selecciona duración aleatoria para transiciones."""
        self.transition_duration = random.uniform(3.0, 5.0)

    def _base_speed(self, cond):
        """Obtiene multiplicador de velocidad base para una condición."""
        return self.multipliers.get(cond, {"speed": 1.0})["speed"]

    def _base_stamina_cost(self, cond):
        """Obtiene multiplicador de costo de resistencia base para una condición."""
        return self.multipliers.get(cond, {"stamina_cost": 0.0})["stamina_cost"]

    # --------------------------
    # Lógica Markov + transición
    # --------------------------
    def _select_next_condition(self):
        """
        Selecciona la siguiente condición climática usando cadena de Markov.
        Basado en la matriz de transición y el estado actual.
        """
        current = self.current_condition
        probs = self.transition_matrix.get(current)

        if not probs:
            self.next_condition = "clear"  # Fallback si no hay transiciones definidas
        else:
            # Seleccionar próximo estado basado en probabilidades
            states = list(probs.keys())
            weights = list(probs.values())
            self.next_condition = random.choices(states, weights=weights, k=1)[0]

        # Iniciar transición si hay cambio de condición
        if self.next_condition != self.current_condition:
            self.transitioning = True
            self.time_since_last_change = 0.0
            self.transition_timer = 0.0
            self._pick_transition_duration()

            # Preparar interpolación desde valores actuales a objetivos
            self.initial_speed_mult = self._base_speed(self.current_condition)
            self.final_speed_mult   = self._base_speed(self.next_condition)
            self.initial_stamina_cost = self._base_stamina_cost(self.current_condition)
            self.final_stamina_cost   = self._base_stamina_cost(self.next_condition)

            # Nueva intensidad aleatoria para la próxima ráfaga
            self.initial_intensity = self.current_intensity
            self.final_intensity   = random.uniform(0.3, 1.0)
        else:
            # Mismo estado, reiniciar temporizador
            self.time_since_last_change = 0.0
            self._reset_burst_timer()

    def update(self, delta_time):
        """
        Actualiza el estado del clima.
        
        Args:
            delta_time: Tiempo transcurrido desde última actualización
        """
        self.time_since_last_change += delta_time

        # Actualizar transición en curso
        if self.transitioning:
            self.transition_timer += delta_time
            if self.transition_timer >= self.transition_duration:
                # Finalizar transición y establecer nuevo estado
                self.transitioning = False
                self.current_condition = self.next_condition
                self.current_intensity = self.final_intensity
                self.transition_timer = 0.0
                self._reset_burst_timer()

        # Verificar si es tiempo de cambiar de condición
        if self.time_since_last_change >= self.burst_timer and not self.transitioning:
            self._select_next_condition()

    # --------------------------
    # Multiplicadores efectivos
    # --------------------------
    def _interp(self, a, b):
        """
        Interpolación lineal entre dos valores según progreso de transición.
        
        Returns:
            Valor interpolado entre a y b
        """
        if not self.transitioning:
            return b  # Si no hay transición, usar valor final
        t = self._clamp(self.transition_timer / self.transition_duration, 0.0, 1.0)
        return a + (b - a) * t

    def _effective_speed_with_intensity(self, base_speed, intensity):
        """
        Aplica penalización por intensidad a la velocidad.
        Más intensidad = menos velocidad.
        
        Returns:
            Velocidad efectiva con penalización aplicada
        """
        # Reducción de hasta 15% extra a máxima intensidad
        eff = base_speed * (1.0 - 0.15 * self._clamp(intensity, 0.0, 1.0))
        return self._clamp(eff, 0.45, 1.0)  # Velocidad mínima del 45%

    def _effective_stamina_with_intensity(self, base_cost, intensity):
        """
        Aumenta el costo de resistencia con la intensidad.
        Más intensidad = mayor costo.
        
        Returns:
            Costo de resistencia efectivo
        """
        # Hasta 70% extra de costo a máxima intensidad
        return base_cost * (1.0 + 0.70 * self._clamp(intensity, 0.0, 1.0))

    def get_speed_multiplier(self):
        """Retorna el multiplicador de velocidad actual con interpolación."""
        if self.transitioning:
            base = self._interp(self.initial_speed_mult, self.final_speed_mult)
            inten = self._interp(self.initial_intensity, self.final_intensity)
            return self._effective_speed_with_intensity(base, inten)
        else:
            base = self._base_speed(self.current_condition)
            return self._effective_speed_with_intensity(base, self.current_intensity)

    def get_stamina_cost_multiplier(self):
        """Retorna el multiplicador de costo de resistencia actual con interpolación."""
        if self.transitioning:
            base = self._interp(self.initial_stamina_cost, self.final_stamina_cost)
            inten = self._interp(self.initial_intensity, self.final_intensity)
            return self._effective_stamina_with_intensity(base, inten)
        else:
            base = self._base_stamina_cost(self.current_condition)
            return self._effective_stamina_with_intensity(base, self.current_intensity)

    # --------------------------
    # Lecturas públicas
    # --------------------------
    def get_current_condition(self):
        """Retorna la condición climática actual."""
        return self.current_condition

    def get_weather_effects_for_courier(self):
        """
        Retorna todos los efectos climáticos para el cálculo del juego.
        
        Returns:
            Dict con multiplicadores y condición actual
        """
        return {
            "speed_multiplier": self.get_speed_multiplier(),
            "stamina_cost_multiplier": self.get_stamina_cost_multiplier(),
            "condition": self.get_current_condition(),
        }

    def get_current_intensity(self):
        """
        Retorna la intensidad actual del clima.
        Útil para HUD o efectos visuales.
        """
        if self.transitioning:
            return self._interp(self.initial_intensity, self.final_intensity)
        return self.current_intensity