import random
import time

class WeatherManager:
    """
    Gestiona el clima en el juego usando una cadena de Markov para las transiciones.
    """
    def __init__(self, weather_data):
        self.data = weather_data.get("data", {})
        self.transition_matrix = self.data.get("transition", {})
        self.initial_condition = self.data.get("initial", {}).get("condition", "clear")
        self.current_condition = self.initial_condition
        self.next_condition = None
        self.current_intensity = self.data.get("initial", {}).get("intensity", 0.0)
        self.transitioning = False
        
        # Multiplicadores para velocidad y consumo de resistencia
        self.multipliers = {
            "clear": {"speed": 1.00, "stamina_cost": 0.0},
            "clouds": {"speed": 0.98, "stamina_cost": 0.0},
            "rain_light": {"speed": 0.90, "stamina_cost": 0.1},
            "rain": {"speed": 0.85, "stamina_cost": 0.1},
            "storm": {"speed": 0.75, "stamina_cost": 0.3},
            "fog": {"speed": 0.88, "stamina_cost": 0.0},
            "wind": {"speed": 0.92, "stamina_cost": 0.1},
            "heat": {"speed": 0.90, "stamina_cost": 0.2},
            "cold": {"speed": 0.92, "stamina_cost": 0.0},
        }

        # Timer para el "burst" de clima
        self.burst_timer = random.uniform(45.0, 60.0)
        self.time_since_last_change = 0.0
        
        # Timer y duración para la transición suave
        self.transition_duration = 5.0 # Segundos de transición
        self.transition_timer = 0.0
        self.initial_speed_mult = 1.0
        self.final_speed_mult = 1.0
        self.initial_stamina_cost = 0.0
        self.final_stamina_cost = 0.0
        
        # Setea la condición inicial
        self.burst_timer = 0 # Para que cambie de inmediato la primera vez
        self.update(0)

    def _select_next_condition(self):
        """Usa la matriz de Markov para sortear la siguiente condición climática."""
        probabilities = self.transition_matrix.get(self.current_condition, {})
        conditions = list(probabilities.keys())
        weights = list(probabilities.values())

        if not conditions:
            # Si no hay transiciones definidas, se queda en el mismo clima
            self.next_condition = self.current_condition
        else:
            self.next_condition = random.choices(conditions, weights=weights)[0]
        
        print(f"Clima cambiando de '{self.current_condition}' a '{self.next_condition}'.")
        self.initial_speed_mult = self.multipliers.get(self.current_condition, {"speed": 1.0})["speed"]
        self.final_speed_mult = self.multipliers.get(self.next_condition, {"speed": 1.0})["speed"]
        self.initial_stamina_cost = self.multipliers.get(self.current_condition, {"stamina_cost": 0.0})["stamina_cost"]
        self.final_stamina_cost = self.multipliers.get(self.next_condition, {"stamina_cost": 0.0})["stamina_cost"]
        
        self.transitioning = True
        self.transition_timer = 0.0
        self.time_since_last_change = 0.0
        self.burst_timer = random.uniform(45.0, 60.0)
        
    def update(self, delta_time):
        """Actualiza el estado del clima y los temporizadores."""
        self.time_since_last_change += delta_time
        
        if self.transitioning:
            self.transition_timer += delta_time
            if self.transition_timer >= self.transition_duration:
                self.transitioning = False
                self.current_condition = self.next_condition
                self.transition_timer = 0.0
        
        if self.time_since_last_change >= self.burst_timer and not self.transitioning:
            self._select_next_condition()
    
    def get_speed_multiplier(self):
        """Calcula y retorna el multiplicador de velocidad actual, con interpolación."""
        if self.transitioning:
            t = self.transition_timer / self.transition_duration
            # Interpolación lineal para un cambio suave
            return self.initial_speed_mult + (self.final_speed_mult - self.initial_speed_mult) * t
        else:
            return self.multipliers.get(self.current_condition, {"speed": 1.0})["speed"]

    def get_stamina_cost_multiplier(self):
        """Calcula y retorna el multiplicador de consumo de resistencia actual."""
        if self.transitioning:
            t = self.transition_timer / self.transition_duration
            return self.initial_stamina_cost + (self.final_stamina_cost - self.initial_stamina_cost) * t
        else:
            return self.multipliers.get(self.current_condition, {"stamina_cost": 0.0})["stamina_cost"]
            
    def get_current_condition(self):
        return self.current_condition