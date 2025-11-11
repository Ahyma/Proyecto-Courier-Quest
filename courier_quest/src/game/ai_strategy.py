import random
import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Tuple, Union 
from game.graph_map import manhattan_distance 

# Esto ayuda a evitar la importación circular, ya que JobsManager y GraphMap
# están siendo usados como Type Hints.
if TYPE_CHECKING:
    from game.ai_courier import AI_Courier 
    from game.jobs_manager import JobsManager
    from game.graph_map import GraphMap
    from game.world import World


class AIStrategy(ABC):
    """
    Clase base abstracta para todas las estrategias de IA (dificultades).
    Define la interfaz para el método decide_and_move.
    """
    @abstractmethod
    def decide_action(self, courier: 'AI_Courier', 
                      game_world: 'World', 
                      jobs_manager: 'JobsManager', 
                      graph_map: 'GraphMap' = None) -> list[Tuple[int, int]]:
        """
        Método que contiene toda la lógica de decisión de la IA. 
        Debe calcular y devolver la ruta completa (lista de tuplas de coordenadas)
        que la IA debe seguir en el siguiente intervalo.
        """
        pass
        
    # ----------------------------------------------------------------------
    # Lógica de Soporte para todas las estrategias
    # (Movemos lógica clave de la antigua AI_Courier aquí)
    # ----------------------------------------------------------------------

    def _manage_job_target(self, courier: 'AI_Courier', current_pos: Tuple[int, int], 
                           jobs_manager: 'JobsManager', graph_map: 'GraphMap' = None) -> bool:
        """
        Lógica unificada para decidir si recoger o entregar un trabajo.
        
        Devuelve True si se realizó una acción (recogida/entrega), False si necesita moverse.
        """
        
        # Nota: La IA debe guardar su objetivo DENTRO de la clase Strategy, no en el Courier.
        # Asumo que las estrategias concretas (Easy, Medium, Hard) tendrán atributos
        # como self.target_position y self.current_job_id_target.
        
        # Este método es complejo, para mantener la refactorización sencilla,
        # lo moveremos a la estrategia del courier (Easy, Medium, Hard)
        # y usaremos los atributos del courier temporalmente hasta refactorizar completamente.
        
        # Si tienes dudas, podemos refactorizar esta parte luego. Por ahora, asumamos que
        # las estrategias (Easy/Medium/Hard) manejan esta lógica directamente.
        return False # Se implementará en las clases hijas
        
        
class EasyStrategy(AIStrategy):
    """Implementa la estrategia de la IA en dificultad FÁCIL."""
    
    def __init__(self):
        # Atributos específicos de la estrategia (donde se guarda el objetivo)
        self.target_position: Tuple[int, int] | None = None
        self.path_to_target: list[Tuple[int, int]] = []
        self.current_job_id_target: str | None = None 
        
    # CÓDIGO CORREGIDO en EasyStrategy. (Devuelve el paso o [])

    def decide_action(self, courier: 'AI_Courier', game_world: 'World', jobs_manager: 'JobsManager', graph_map: 'GraphMap' = None) -> list[Tuple[int, int]]:
        
        current_pos = (courier.x, courier.y)
        
        # 1. Recuperación de Stamina: Si está exhausto, no puede hacer nada.
        if courier.is_exhausted:
            return [] 
            
        # 2. Decidir objetivo (Recoger o Entregar)
        if self._manage_job_target(courier, current_pos, jobs_manager):
            return [] # Acción completada (recogida/entrega), no moverse en este tick

        # 3. Movimiento: Si tiene un objetivo, devolver el siguiente paso aleatorio.
        if self.target_position:
            adj_cells = game_world.get_adjacent_walkable_cells(courier.x, courier.y) 
            
            if adj_cells:
                # Elegir una dirección aleatoria de calle adyacente
                next_x, next_y = random.choice(adj_cells)
                
                # ➡️ RETORNAR LA RUTA (UN SOLO PASO) EN LUGAR DE LLAMAR A move()
                return [(next_x, next_y)]
        
        return [] # No hay objetivo ni movimiento
        
    def _manage_job_target(self, courier: 'AI_Courier', current_pos: Tuple[int, int], jobs_manager: 'JobsManager') -> bool:
        """
        Lógica unificada para decidir si recoger o entregar un trabajo (versión simplificada).
        Se movió aquí para que la EasyStrategy maneje sus propios atributos de objetivo.
        """
        
        if not courier.has_jobs():
            # No tiene pedidos: buscar un pedido para recoger
            if not self.current_job_id_target:
                available_jobs = jobs_manager.get_available_jobs()
                
                if available_jobs:
                    chosen_job = available_jobs[0] # Elegir el primero disponible (EASY)
                        
                    # Establecer el nuevo objetivo de recogida
                    self.current_job_id_target = chosen_job.id
                    self.target_position = chosen_job.pickup_pos
                else:
                    self.target_position = None
                    self.current_job_id_target = None
                    
            # Intentar recoger si está en la posición objetivo 
            if self.current_job_id_target:
                job_to_pickup = jobs_manager.get_job_by_id(self.current_job_id_target)
                
                if job_to_pickup and current_pos == job_to_pickup.pickup_pos:
                    if courier.can_pickup_job(job_to_pickup):
                        # Nota: Aquí llamamos a try_pickup_job del jobs_manager para la interacción
                        # La llamada real a la interacción se hace al final de courier.move, 
                        # pero la IA a menudo necesita el método directo para forzar la recogida/entrega.
                        
                        # Usar el método de JobsManager que ya habías implementado para IA
                        if jobs_manager.attempt_pickup(courier, job_to_pickup):
                            # Si la recogida fue exitosa, el nuevo objetivo es la entrega
                            self.target_position = job_to_pickup.dropoff_pos
                            self.current_job_id_target = None
                            return True # Acción completada (recogida)
                        else:
                            # Si no puede recogerlo (p.ej., por peso), cancelar objetivo y buscar otro
                            self.current_job_id_target = None
                            self.target_position = None
                            return True # Se intentó una acción (fallida)
                        
        else: 
            # Tiene pedidos: el objetivo es el punto de entrega del trabajo actual
            current_job = courier.get_current_job()
            if current_job:
                self.target_position = current_job.dropoff_pos
                
                # Intentar entregar si está en la posición objetivo
                if current_pos == current_job.dropoff_pos:
                    # Usar el método de JobsManager que ya habías implementado para IA
                    if jobs_manager.attempt_delivery(courier, current_job):
                        self.target_position = None # Objetivo completado
                        return True # Acción completada (entrega)

        return False # No se realizó ninguna acción (el objetivo es moverse)




class MediumStrategy(EasyStrategy):
    """Implementa la estrategia del vecino más cercano (IA MEDIA)."""
    def decide_action(self, courier: 'AI_Courier', game_world: 'World', jobs_manager: 'JobsManager', graph_map: 'GraphMap' = None) -> list[Tuple[int, int]]:
    
        current_pos = (courier.x, courier.y)
        
        if courier.is_exhausted:
            return [] 
            
        # 1. Decidir objetivo (Recoger o Entregar)
        if self._manage_job_target(courier, current_pos, jobs_manager):
            return [] 
            
        # 2. Movimiento: Elegir el movimiento adyacente con la mejor puntuación.
        if self.target_position:
            adj_cells = game_world.get_adjacent_walkable_cells(courier.x, courier.y) 
            
            best_move = None
            min_score = float('inf') 
            
            # ➡️ LÍNEA DE DEPURACIÓN (1)
            print(f"MEDIUM DEBUG: Posición actual: {current_pos}, Objetivo: {self.target_position}")
            
            for next_x, next_y in adj_cells:
                next_pos = (next_x, next_y)
                
                # 2a. Calcular el costo real de moverse a esta celda
                if courier.graph_map is None:
                    continue
                    
                cost = courier.graph_map.calculate_move_cost_for_courier(courier, (courier.x, courier.y), next_pos)
                
                # CRÍTICO: Si el costo es infinito (por edificio), esta celda debe ser IGNORADA.
                # Aunque adj_cells solo trae celdas caminables, si calculate_move_cost... tiene otra lógica,
                # esta verificación es vital. Si chocas, este es el problema.
                if cost == float('inf'):
                    # ➡️ LÍNEA DE DEPURACIÓN (2) - Deberías ver esto si chocas.
                    print(f"MEDIUM DEBUG: Movimiento a {next_pos} descartado: Costo INFINITO (Edificio).")
                    continue
                    
                # 2b. Calcular la heurística (distancia Manhattan al objetivo)
                heuristic = manhattan_distance(next_pos, self.target_position) 
                
                # Estrategia Greedy/Heurística: Probamos con un valor aún más alto para la heurística.
                # Forzamos a la IA a priorizar la dirección correcta sobre el ahorro de estamina a corto plazo.
                score = cost + heuristic * 2.0  # <--- AUMENTAMOS EL PESO DE LA HEURÍSTICA A 2.0
                
                # ➡️ LÍNEA DE DEPURACIÓN (3)
                print(f"MEDIUM DEBUG: Movimiento a {next_pos} | Costo: {cost:.2f} | Heurística: {heuristic:.1f} | SCORE: {score:.2f}")

                if score < min_score:
                    min_score = score
                    best_move = next_pos
                    
            if best_move:
                # ➡️ LÍNEA DE DEPURACIÓN (4)
                print(f"MEDIUM DEBUG: Mejor movimiento elegido: {best_move} con Score: {min_score:.2f}")
                return [best_move]
            
            # ➡️ LÍNEA DE DEPURACIÓN (5) - Esto aparecerá si solo hay edificios alrededor.
            print("MEDIUM DEBUG: No se pudo elegir un movimiento válido.")
            
        return [] # No hay objetivo ni movimiento
    
    
class HardStrategy(MediumStrategy):
    """Implementa la estrategia de optimización de ruta A* y rentabilidad (IA DIFÍCIL)."""
    
    # CÓDIGO CORREGIDO en HardStrategy

    def decide_action(self, courier: 'AI_Courier', game_world: 'World', jobs_manager: 'JobsManager', graph_map: 'GraphMap' = None) -> list[Tuple[int, int]]:
        
        current_pos = (courier.x, courier.y)
        
        if courier.is_exhausted:
            return [] 

        # 1. Si no tiene una ruta planificada o está al final de la ruta, replanificar
        is_path_stale = not self.path_to_target or self.path_to_target[0] == current_pos
        
        if is_path_stale:
            
            # Intentar realizar acción (Recoger o Entregar)
            if self._manage_job_target_hard(courier, current_pos, jobs_manager):
                return [] # Acción completada, no moverse en este tick

            # Si se necesita movimiento, calcular la ruta A*
            if self.target_position:
                if courier.graph_map is None: return [] # Fallback
                
                # Recalcular la ruta óptima usando A*
                path_result_tuple = courier.graph_map.find_shortest_path(current_pos, self.target_position, courier=courier)
                
                path = path_result_tuple[0] if path_result_tuple else None
                
                if path and len(path) > 1:
                    # El camino incluye la posición actual, así que la eliminamos
                    self.path_to_target = path[1:]
                else:
                    self.path_to_target = [] # No se encontró ruta
            else:
                self.path_to_target = []

        # 2. Moverse: Devolver la ruta planificada (la ruta completa menos el punto actual)
        # ➡️ RETORNAR LA RUTA COMPLETA PARA QUE AI_Courier.update LA GESTIONE
        return self.path_to_target
# EN HardStrategy._manage_job_target_hard (en src/game/ai_strategy.py)

    def _manage_job_target_hard(self, courier: 'AI_Courier', current_pos: Tuple[int, int], jobs_manager: 'JobsManager') -> bool:
        
        # 1. Intentar Entregar (La misma lógica para todos: usar el método del padre, EasyStrategy)
        if courier.has_jobs():
            # Llama a la implementación de EasyStrategy (padre) para manejar la interacción (recoger/entregar)
            if super()._manage_job_target(courier, current_pos, jobs_manager):
                # Si el padre realizó una acción (entrega), retornamos True
                return True
            # Si tiene trabajos, pero no está en la posición de entrega, necesita moverse.
            # No hacemos más aquí; dejamos que decide_action calcule la ruta.
            return False # Necesita moverse (no realizó una acción)
                
        # 2. Intentar Recoger (Lógica HARD: Rentabilidad)
        # Solo buscamos un nuevo trabajo si NO tenemos un objetivo de recogida (current_job_id_target)
        if not self.current_job_id_target:
            available_jobs = jobs_manager.get_available_jobs()
            
            if available_jobs and courier.graph_map:
                # IA DIFÍCIL: Elegir el más rentable
                chosen_job = self._choose_most_profitable_job(courier, current_pos, available_jobs, courier.graph_map)
            else:
                # Fallback o si no hay trabajos
                chosen_job = None
                    
            if chosen_job:
                # Establecer el nuevo objetivo de recogida
                self.current_job_id_target = chosen_job.id
                self.target_position = chosen_job.pickup_pos
            else:
                self.target_position = None
                self.current_job_id_target = None
                        
        # 3. Si tenemos un objetivo (ya sea recién seleccionado o anterior),
        # verificamos si hemos llegado al punto de recogida. 
        # Usamos la lógica de interacción del padre para manejar la recogida si estamos encima de la posición.
        if self.current_job_id_target:
            # Llamamos al padre para verificar la interacción de recogida
            if super()._manage_job_target(courier, current_pos, jobs_manager):
                return True # Recogida exitosa.

        return False # No hay trabajo, no se realizó ninguna acción, y/o se necesita movimiento.
        
    def _choose_most_profitable_job(self, courier: 'AI_Courier', current_pos: Tuple[int, int], available_jobs: list, graph_map: 'GraphMap'):
        """
        Calcula la rentabilidad (PAGO / COSTO_DE_STAMINA) de cada trabajo disponible
        y elige el mejor. (Misma lógica que tenías)
        """
        best_job = None
        max_profitability = -1.0
        
        for job in available_jobs:
            
            # 1. Verificar capacidad de peso
            if courier.current_weight + job.weight > courier.max_weight:
                continue 
            
            # 2. Calcular el costo de la ruta (Stamina)
            pickup_location = job.pickup_pos
            
            # Intentar encontrar la ruta A* y su costo
            path_result, cost_stamina = graph_map.find_shortest_path(current_pos, pickup_location, courier=courier, return_cost=True)
            
            if path_result is None or cost_stamina == float('inf'):
                # ➡️ LÍNEA DE DEPURACIÓN: Muestra si no se pudo encontrar una ruta
                print(f"HARD DEBUG: Ruta NO encontrada para el trabajo {job.id} (Costo: {cost_stamina}).")
                continue
                
            # 3. Calcular la rentabilidad
            cost_divisor = max(cost_stamina, 1.0) 
            profitability = job.payout / cost_divisor
            
            # 4. Actualizar el mejor trabajo
            if profitability > max_profitability:
                max_profitability = profitability
                best_job = job
                
        # ➡️ LÍNEA DE DEPURACIÓN: Muestra el resultado final de la selección
        print(f"HARD DEBUG: Trabajo más rentable elegido: {best_job.id if best_job else 'NONE'}. Rentabilidad máxima: {max_profitability:.2f}")
        
        return best_job