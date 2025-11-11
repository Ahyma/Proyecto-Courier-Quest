from game.courier import Courier
from game.graph_map import GraphMap
from enum import Enum
# Importamos la clase base de estrategia que definiremos después
from game.ai_strategy import AIStrategy # <--- ¡Nueva Importación!

# Definición de los niveles de dificultad para mayor claridad
class AIDifficulty(Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"

class AI_Courier(Courier):
    """
    Representa un repartidor controlado por la Inteligencia Artificial (CPU).
    Utiliza el Patrón Strategy para externalizar la lógica de decisión
    según el nivel de dificultad.
    """
    
    def __init__(self, start_x, start_y, image, difficulty=AIDifficulty.EASY,
                 max_stamina=100, base_speed=3.0, max_weight=10, 
                 graph_map: GraphMap = None):

        # Llama al constructor de la clase base (Courier)
        super().__init__(start_x, start_y, image, max_stamina, base_speed, max_weight)
        
        # Atributos específicos de la IA
        self.difficulty = difficulty
        self.graph_map = graph_map 
        
        # El objeto que contendrá la lógica de decisión (se asigna después)
        self.strategy: AIStrategy = None 
        
        # La IA ya no necesita target_position ni path_to_target, eso lo manejará la estrategia.
        
        # temporizadores para throttling de la IA
        self.move_timer = 0.0
        self.action_timer = 0.0
        self.ACTION_DECIDE_INTERVAL = 0.2  # segundos entre decisiones (ajusta si hace falta)
        self.current_path = []  # lista de (x,y) pasos a seguir
        
    def set_strategy(self, strategy):
        """Asignar/actualizar la estrategia utilizada por la IA."""
        self.strategy = strategy

    def decide_action(self, game_world, jobs_manager, graph_map=None):
        """Delegar la decisión a la estrategia asignada (compatibilidad con varios nombres)."""
        # Si la estrategia fue asignada, intentar llamar a alguno de sus métodos comunes
        if hasattr(self, "strategy") and self.strategy:
            for name in ("decide_action", "decide", "choose_action", "select_target", "get_action", "act"):
                if hasattr(self.strategy, name) and callable(getattr(self.strategy, name)):
                    fn = getattr(self.strategy, name)
                    try:
                        # algunas estrategias esperan (ai, game_world, jobs_manager, graph_map)
                        return fn(self, game_world, jobs_manager, graph_map)
                    except TypeError:
                        # otras esperan (game_world, jobs_manager, graph_map)
                        try:
                            return fn(game_world, jobs_manager, graph_map)
                        except TypeError:
                            # última oportunidad: solo pasar self
                            try:
                                return fn(self)
                            except Exception:
                                pass
        # Sin estrategia o ningún método compatible: fallback simple (no acción)
        return [] # <--- DEBE DEVOLVER UNA LISTA VACÍA
            
    def update(self, delta_time, game_world, weather_manager, jobs_manager):
        """Update llamado desde main; throttlea decisiones y realiza 1 paso por intervalo."""
        # Recuperar stamina (usa misma lógica que jugador)
        current_tile_type = game_world.tiles[self.y][self.x] if (0 <= self.y < game_world.height and 0 <= self.x < game_world.width) else "C"
        is_resting_spot = (current_tile_type == "P")
        if hasattr(self, "recover_stamina"):
            self.recover_stamina(delta_time, is_resting_spot)

        # actualizar timers
        self.move_timer += delta_time
        self.action_timer += delta_time

        # Decidir acción periódicamente (no cada frame)
        if self.action_timer >= self.ACTION_DECIDE_INTERVAL:
            self.action_timer = 0.0
            # decide_action debería rellenar/actualizar self.current_path o devolver un acción concreta
            decision = self.decide_action(game_world, jobs_manager, game_world.graph_map if hasattr(game_world, "graph_map") else None)
            # Si decide_action devuelve una ruta, usarla
            if isinstance(decision, list) and decision:
                self.current_path = decision

        # Si hay una ruta, mover un paso respetando el tiempo por casilla
        if self.current_path:
            # calcular tiempo necesario para moverse 1 casilla (mismo método que jugador)
            try:
                move_delay = self.get_time_per_tile(game_world, weather_manager)
            except Exception:
                move_delay = 0.2

            if self.move_timer >= move_delay:
                next_pos = self.current_path.pop(0)
                nx, ny = next_pos
                dx, dy = nx - self.x, ny - self.y

                # comprobar stamina antes de intentar mover
                if getattr(self, "stamina", 1) <= 0:
                    # sin stamina: no mover, esperar recuperación
                    self.move_timer = 0.0
                    return

                # calcular parámetros como hace el jugador
                stamina_cost_modifier = weather_manager.get_stamina_cost_multiplier()
                climate_mult = weather_manager.get_speed_multiplier()
                surface_weight = game_world.surface_weight_at(nx, ny)

                # usar el método move para aplicar costes y colisiones (no asignar x/y directamente)
                # firma flexible: algunos move aceptan (dx,dy,game_world,jobs_manager) y otros kwargs
                try:
                    # intentar con kwargs (coincide con llamadas en main)
                    self.move(
                        dx,
                        dy,
                        stamina_cost_modifier=stamina_cost_modifier,
                        surface_weight=surface_weight,
                        climate_mult=climate_mult,
                        game_world=game_world,  # si tu move no usa este arg, Python lo ignorará si la firma lo permite
                    )
                except TypeError:
                    # fallback a la firma (dx,dy,game_world,jobs_manager)
                    self.move(dx, dy, game_world, jobs_manager)

                # reset del timer de movimiento
                self.move_timer = 0.0

    # El método decide_action ya no existe aquí, se mueve a la estrategia.
    def get_save_state(self):
        """Compatibilidad: devuelve el estado para guardado.
        Intenta llamar al método del padre si existe, luego busca nombres alternativos y finalmente arma un dict.
        """
        # 1) Si la clase hereda y el padre define get_save_state
        try:
            return super().get_save_state()
        except Exception:
            pass

        # 2) Buscar métodos alternativos comunes
        for name in ("save_state", "to_dict", "serialize", "state_dict", "get_state"):
            if hasattr(self, name):
                fn = getattr(self, name)
                if callable(fn):
                    try:
                        return fn()
                    except Exception:
                        pass

        # 3) Fallback manual (campos mínimos)
        return {
            "x": getattr(self, "x", 0),
            "y": getattr(self, "y", 0),
            "stamina": getattr(self, "stamina", 0),
            "income": getattr(self, "income", 0),
            "reputation": getattr(self, "reputation", 0),
            "packages_delivered": getattr(self, "packages_delivered", 0),
            "_clean_streak": getattr(self, "_clean_streak", 0),
        }