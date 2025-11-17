# courier_quest/src/game/weather.py

"""
import time: para manejar tiempos y duraciones
import random: para generar números aleatorios
"""
import time
import random

""" 
Módulo de gestión del clima con ráfagas aleatorias y transiciones suaves

Proporciona la clase WeatherManager que controla el estado climático actual,
las transiciones entre condiciones y el cálculo del multiplicador de velocidad asociado

Las condiciones climáticas afectan la velocidad de movimiento del courier, haciendo que
moverse sobre el mapa sea más lento o más rápido según el clima actual
"""
__all__ = ["WeatherManager"]  # export explícito del símbolo WeatherManager

# ------------------------------------------------------------------------------------
# Multiplicadores de velocidad según condición climática
# ------------------------------------------------------------------------------------
MULTS = {
    "clear": 1.00, 
    "clouds": 0.98, 
    "rain_light": 0.90, 
    "rain": 0.85,
    "storm": 0.75, 
    "fog": 0.88, 
    "wind": 0.92, 
    "heat": 0.90, 
    "cold": 0.92
}

# ------------------------------------------------------------------------------------
# Matriz de transición por defecto (si no viene una en weather.json)
# ------------------------------------------------------------------------------------
"""
Este bloque es para definir la matriz de transición por defecto entre condiciones climáticas
Cada clave es una condición actual, y su valor es un diccionario con las posibles condiciones siguientes y sus probabilidades asociadas
Por ejemplo, desde "clear" hay un 60% de probabilidad de seguir "clear", 30% de pasar a "clouds" y 10% a "rain"
"""
DEFAULT_TRANSITION = {
    "clear":  {"clear": 0.6, "clouds": 0.3, "rain": 0.1},
    "clouds": {"clear": 0.3, "clouds": 0.5, "rain": 0.2},
    "rain":   {"clear": 0.2, "clouds": 0.4, "rain": 0.4},
}

# ------------------------------------------------------------------------------------
# Clase principal de gestión del clima
# ------------------------------------------------------------------------------------
class WeatherManager:
    """
    Controla el clima con ráfagas aleatorias y transiciones suaves.
    - burst_range: duración aleatoria de cada ráfaga (45–60 s por defecto)
    - transition_secs: segundos que dura la transición (fade in/out)
    """

    def __init__(self, weather_data=None, burst_range=(45, 60), transition_secs=4.0):
        d = (weather_data or {}).get("data", {})
        self.transition = d.get("transition_matrix", DEFAULT_TRANSITION)

        initial = d.get("initial", {"condition": "clear", "intensity": 0.0})
        self.curr = initial.get("condition", "clear")
        self.next = self.curr
        self.intensity = float(initial.get("intensity", 0.0))

        self.burst_min, self.burst_max = burst_range
        self.transition_secs = float(transition_secs)

        """control de tiempo"""
        self._t0 = time.time()
        self._set_new_burst()

        """blending"""
        self._blend_from = MULTS.get(self.curr, 1.0)
        self._blend_to = self._blend_from
        self._blend_start = time.time()
        self._blending = False
        self._interp_mult = self._blend_from

    def _set_new_burst(self):
        """Define una nueva duración de ráfaga."""
        self.burst_dur = random.randint(self.burst_min, self.burst_max)

    def _sample_next_condition(self):
        """Escoge la siguiente condición según la matriz de transición
        
        Primero obtiene la fila correspondiente a la condición actual
        Luego, usa las probabilidades para seleccionar aleatoriamente la siguiente condición
        Si no hay fila (condición desconocida), retorna una condición aleatoria
        """
        row = self.transition.get(self.curr, {})
        if not row:
            return random.choice(list(MULTS.keys()))
        conds = list(row.keys())
        probs = list(row.values())
        total = sum(probs) or 1.0
        probs = [p / total for p in probs]
        r = random.random()
        acc = 0.0
        for c, p in zip(conds, probs):
            acc += p
            if r <= acc:
                return c
        return conds[-1]

    def update(self):
        """Actualiza el estado del clima, aplicando transición si corresponde."""
        now = time.time()

        """¿terminó la ráfaga actual? -> iniciar transición"""
        if (now - self._t0) >= self.burst_dur and not self._blending:
            self.next = self._sample_next_condition()
            self._blend_from = MULTS.get(self.curr, 1.0)
            self._blend_to   = MULTS.get(self.next, 1.0)
            self._blend_start = now
            self._blending = True

        """Transición suave (interpolación lineal)"""
        if self._blending:
            t = (now - self._blend_start) / self.transition_secs
            if t >= 1.0:
                self.curr = self.next
                self._blending = False
                self._t0 = now
                self._set_new_burst()
                self._interp_mult = MULTS.get(self.curr, 1.0)
            else:
                self._interp_mult = self._blend_from + t * (self._blend_to - self._blend_from)
        else:
            self._interp_mult = MULTS.get(self.curr, 1.0)

    def speed_multiplier(self) -> float:
        """Multiplicador de velocidad actual (interpolado)."""
        return float(self._interp_mult)

    def label(self) -> str:
        """Nombre de la condición climática actual: 'clear', 'rain', etc."""
        return self.curr
