"""
import random
import time

class WeatherManager:
    
    #Gestiona el clima en el juego usando una cadena de Markov para las transiciones.
    #Aplica multiplicadores de velocidad y costo de resistencia basados en la condición actual.
    
    def __init__(self, weather_data):
        self.data = weather_data.get("data", {})
        
        # Cargamos la matriz de transición del JSON
        transition_matrix = self.data.get("transition", {})
        
        # --- Ajuste de probabilidades de 'clear' para un clima más dinámico ---
        # (Ajuste del paso anterior: reduce clear->clear de 0.6 a 0.5)
        if "clear" in transition_matrix:
            print("Ajustando probabilidades de 'clear' para un clima más dinámico.")
            # Nuevas probabilidades (la suma debe ser 1.0)
            transition_matrix["clear"] = {
                "clear": 0.5,        
                "clouds": 0.4,       
                "rain_light": 0.1    
            }
        
        self.transition_matrix = transition_matrix

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
            "wind": {"speed": 0.92, "stamina_cost": 0.05},
            "heat": {"speed": 0.95, "stamina_cost": 0.2},
            "cold": {"speed": 0.90, "stamina_cost": 0.0}
        }
        
        # --- MODIFICACIÓN DE DURACIÓN ---
        # Aumenta el tiempo que dura cada estado de clima
        self.burst_timer = 20.0  # Tiempo que dura cada estado de clima (en segundos)
        self.transition_duration = 5.0 # Duración de la transición suave entre estados (en segundos)
        self.time_since_last_change = 0.0
        self.transition_timer = 0.0
        
        # Variables de interpolación (se inicializan al empezar una transición)
        self.initial_speed_mult = 1.0
        self.final_speed_mult = 1.0
        self.initial_stamina_cost = 0.0
        self.final_stamina_cost = 0.0

    def _select_next_condition(self):
        
        #Selecciona la siguiente condición climática basada en la matriz de transición.
        
        current_state = self.current_condition
        possible_next_states = self.transition_matrix.get(current_state)
        
        if not possible_next_states:
            self.next_condition = "clear"
        else:
            states = list(possible_next_states.keys())
            probabilities = list(possible_next_states.values())
            
            chosen_state = random.choices(states, weights=probabilities, k=1)[0]
            self.next_condition = chosen_state
        
        if self.next_condition != self.current_condition:
            print(f"Clima cambiando de '{self.current_condition}' a '{self.next_condition}'.")
            self.transitioning = True
            self.time_since_last_change = 0.0
            
            # Inicializa variables de interpolación para el cambio suave
            self.initial_speed_mult = self.multipliers.get(self.current_condition, {"speed": 1.0})["speed"]
            self.final_speed_mult = self.multipliers.get(self.next_condition, {"speed": 1.0})["speed"]
            
            self.initial_stamina_cost = self.multipliers.get(self.current_condition, {"stamina_cost": 0.0})["stamina_cost"]
            self.final_stamina_cost = self.multipliers.get(self.next_condition, {"stamina_cost": 0.0})["stamina_cost"]
        else:
             # Si no hay cambio, reinicia el temporizador para sortear de nuevo
            self.time_since_last_change = 0.0
            print(f"Clima se mantiene en '{self.current_condition}'.")


    def update(self, delta_time):
        
        #Actualiza el estado del clima y gestiona las transiciones.
        
        self.time_since_last_change += delta_time
        
        if self.transitioning:
            self.transition_timer += delta_time
            if self.transition_timer >= self.transition_duration:
                self.transitioning = False
                self.current_condition = self.next_condition
                self.transition_timer = 0.0
        
        # El cambio se sortea solo si ha pasado el tiempo del burst_timer y no hay una transición activa
        if self.time_since_last_change >= self.burst_timer and not self.transitioning:
            self._select_next_condition()
    
    def get_speed_multiplier(self):
        #Calcula y retorna el multiplicador de velocidad actual, con interpolación.
        if self.transitioning:
            t = self.transition_timer / self.transition_duration
            # Interpolación lineal para un cambio suave
            return self.initial_speed_mult + (self.final_speed_mult - self.initial_speed_mult) * t
        else:
            return self.multipliers.get(self.current_condition, {"speed": 1.0})["speed"]

    def get_stamina_cost_multiplier(self):
        #Calcula y retorna el multiplicador de consumo de resistencia actual.
        if self.transitioning:
            t = self.transition_timer / self.transition_duration
            return self.initial_stamina_cost + (self.final_stamina_cost - self.initial_stamina_cost) * t
        else:
            return self.multipliers.get(self.current_condition, {"stamina_cost": 0.0})["stamina_cost"]

    def get_current_condition(self):
        #Retorna la condición climática actual.
        return self.current_condition

    def get_weather_effects_for_courier(self):
        #Retorna los efectos completos del clima para el cálculo de juego.
        return {
            "speed_multiplier": self.get_speed_multiplier(),
            "stamina_cost_multiplier": self.get_stamina_cost_multiplier(),
            "condition": self.get_current_condition()
        }
"""

import random

class WeatherManager:
    """
    Gestiona el clima con cadena de Markov, ráfagas 45–60 s e intensidad (0–1).
    Incluye transición suave (3–5 s) interpolando multiplicadores.
    """
    def __init__(self, weather_data):
        self.data = weather_data.get("data", {})
        self.transition_matrix = self.data.get("transition", {}) or {}

        # Ajuste opcional para que 'clear' sea menos pegajoso y aparezca 'rain_light'
        if "clear" in self.transition_matrix:
            self.transition_matrix["clear"] = {
                "clear": 0.5,
                "clouds": 0.4,
                "rain_light": 0.1
            }

        # Estado actual
        initial = self.data.get("initial", {})
        self.current_condition = initial.get("condition", "clear")
        self.current_intensity = float(initial.get("intensity", 0.0))  # 0–1
        self.next_condition = None
        self.transitioning = False

        # Tabla base de multiplicadores (sin intensidad)
        self.multipliers = {
            "clear":      {"speed": 1.00, "stamina_cost": 0.00},
            "clouds":     {"speed": 0.98, "stamina_cost": 0.00},
            "rain_light": {"speed": 0.90, "stamina_cost": 0.10},
            "rain":       {"speed": 0.85, "stamina_cost": 0.10},
            "storm":      {"speed": 0.75, "stamina_cost": 0.30},
            "fog":        {"speed": 0.88, "stamina_cost": 0.00},
            "wind":       {"speed": 0.92, "stamina_cost": 0.05},
            "heat":       {"speed": 0.90, "stamina_cost": 0.20},
            "cold":       {"speed": 0.92, "stamina_cost": 0.00},
        }

        # Timers
        self._reset_burst_timer()             # 45–60 s
        self.transition_duration = 4.0        # valor inicial (se randomiza en cada cambio)
        self.time_since_last_change = 0.0
        self.transition_timer = 0.0

        # Variables de interpolación
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
        return max(lo, min(hi, x))

    def _reset_burst_timer(self):
        self.burst_timer = random.uniform(45.0, 60.0)

    def _pick_transition_duration(self):
        self.transition_duration = random.uniform(3.0, 5.0)

    def _base_speed(self, cond):
        return self.multipliers.get(cond, {"speed": 1.0})["speed"]

    def _base_stamina_cost(self, cond):
        return self.multipliers.get(cond, {"stamina_cost": 0.0})["stamina_cost"]

    # --------------------------
    # Lógica Markov + transición
    # --------------------------
    def _select_next_condition(self):
        current = self.current_condition
        probs = self.transition_matrix.get(current)

        if not probs:
            self.next_condition = "clear"
        else:
            states = list(probs.keys())
            weights = list(probs.values())
            self.next_condition = random.choices(states, weights=weights, k=1)[0]

        # Si hay cambio, iniciar transición
        if self.next_condition != self.current_condition:
            self.transitioning = True
            self.time_since_last_change = 0.0
            self.transition_timer = 0.0
            self._pick_transition_duration()

            # Preparar interpolación (desde actuales a objetivos)
            self.initial_speed_mult = self._base_speed(self.current_condition)
            self.final_speed_mult   = self._base_speed(self.next_condition)
            self.initial_stamina_cost = self._base_stamina_cost(self.current_condition)
            self.final_stamina_cost   = self._base_stamina_cost(self.next_condition)

            # Nueva intensidad 0.3–1.0 para la próxima ráfaga
            self.initial_intensity = self.current_intensity
            self.final_intensity   = random.uniform(0.3, 1.0)
        else:
            # Se mantiene, reiniciar temporizador de ráfaga
            self.time_since_last_change = 0.0
            self._reset_burst_timer()

    def update(self, delta_time):
        """Actualiza timers y gestiona el inicio/fin de transiciones."""
        self.time_since_last_change += delta_time

        if self.transitioning:
            self.transition_timer += delta_time
            if self.transition_timer >= self.transition_duration:
                # Fijar nuevo estado al terminar transición
                self.transitioning = False
                self.current_condition = self.next_condition
                self.current_intensity = self.final_intensity
                self.transition_timer = 0.0
                self._reset_burst_timer()

        # ¿Toca iniciar un nuevo sorteo?
        if self.time_since_last_change >= self.burst_timer and not self.transitioning:
            self._select_next_condition()

    # --------------------------
    # Multiplicadores efectivos
    # --------------------------
    def _interp(self, a, b):
        """Interpolación lineal entre a y b según progreso de transición."""
        if not self.transitioning:
            return b
        t = self._clamp(self.transition_timer / self.transition_duration, 0.0, 1.0)
        return a + (b - a) * t

    def _effective_speed_with_intensity(self, base_speed, intensity):
        """
        Aplica penalización por intensidad a la velocidad.
        Más intensidad => un poco menos de velocidad.
        """
        # Reducción de hasta 15% extra a máxima intensidad
        eff = base_speed * (1.0 - 0.15 * self._clamp(intensity, 0.0, 1.0))
        return self._clamp(eff, 0.45, 1.0)

    def _effective_stamina_with_intensity(self, base_cost, intensity):
        """
        Aumenta el costo de resistencia con la intensidad.
        Más intensidad => mayor costo.
        """
        # Hasta 70% extra de costo a máxima intensidad
        return base_cost * (1.0 + 0.70 * self._clamp(intensity, 0.0, 1.0))

    def get_speed_multiplier(self):
        if self.transitioning:
            base = self._interp(self.initial_speed_mult, self.final_speed_mult)
            inten = self._interp(self.initial_intensity, self.final_intensity)
            return self._effective_speed_with_intensity(base, inten)
        else:
            base = self._base_speed(self.current_condition)
            return self._effective_speed_with_intensity(base, self.current_intensity)

    def get_stamina_cost_multiplier(self):
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
        return self.current_condition

    def get_weather_effects_for_courier(self):
        return {
            "speed_multiplier": self.get_speed_multiplier(),
            "stamina_cost_multiplier": self.get_stamina_cost_multiplier(),
            "condition": self.get_current_condition(),
        }

    # (opcional) por si quisieras pintarla en HUD/visuals
    def get_current_intensity(self):
        if self.transitioning:
            return self._interp(self.initial_intensity, self.final_intensity)
        return self.current_intensity

"""
Esta versión incluye:
- Markov + ráfagas aleatorias de 45–60s
- Transiciones suaves de 3–5s interpolando multiplicadores (o sea get_speed_multiplier() y get_stamina_cost_multiplier() ya no devuelven valores fijos instantáneos, sino que varían suavemente)
- Intensidad (0–1) que afecta a velocidad y resistencia
- Ajuste opcional para que 'clear' sea menos pegajoso y aparezca 'rain_light'. 
    - Pegajoso = que tienda a quedarse en el mismo estado.
"""