import math
import heapq
import sys
from game.courier import Courier # Importar Courier para acceder a atributos de peso/velocidad

# Definición de la heurística de distancia de Manhattan
# (Para evitar depender de una función dentro de la clase)
def manhattan_distance(start: tuple[int, int], end: tuple[int, int]) -> float:
    """Calcula la distancia de Manhattan entre dos puntos (x, y)."""
    return abs(start[0] - end[0]) + abs(start[1] - end[1])

class GraphMap:
    """
    Representa el mapa del juego como un grafo para algoritmos de búsqueda.
    Utiliza A* para encontrar la ruta óptima minimizando el costo de stamina/tiempo.
    """
    
    def __init__(self, game_world):
        """Inicializa el grafo a partir de la instancia de World."""
        self.world = game_world
        self.width = game_world.width
        self.height = game_world.height
        
        # El grafo se define implícitamente por el World
        
    def _get_neighbors(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        """
        Retorna las celdas adyacentes (vecinas) que están dentro de los límites del mapa.
        La verificación de transitabilidad (edificios) se maneja en calculate_move_cost_for_courier.
        """
        x, y = pos
        neighbors = []
        
        # Movimiento ortogonal (arriba, abajo, izquierda, derecha)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            
            # Solo verificar límites del mapa
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbors.append((nx, ny))
                    
        return neighbors

    def calculate_move_cost_for_courier(self, courier: 'AI_Courier', start_pos: tuple[int, int], end_pos: tuple[int, int]) -> float:
        """
        Calcula el costo (en stamina) de moverse de start_pos a end_pos para un courier,
        incluyendo el manejo de celdas intransitables (costo infinito).
        """
        end_x, end_y = end_pos
        
        # CRÍTICO: 1. Verificar si la celda de destino es transitable
        # Si no es transitable, el costo es infinito.
        if not self.world.is_walkable(end_x, end_y):
            return float('inf')

        # 2. Obtener el multiplicador base de la superficie (ej. calle vs. pasto)
        surface_weight = self.world.surface_weight_at(end_x, end_y)
        
        # 3. Aplicar el costo base y la influencia de la superficie
        base_cost = 1.0
        # Un valor menor a 1.0 en surface_weight (ej. pasto) hará que el costo aumente (movimiento lento).
        final_cost = base_cost / surface_weight 
        
        # 4. Aplicar penalizaciones del Courier (peso)
        weight_penalty = courier.current_weight / courier.max_weight
        # El costo aumenta con el peso, penalizando más el movimiento
        final_cost *= (1.0 + weight_penalty * 0.5)
            
        # [Si tienes WeatherManager, la lógica del clima iría aquí]

        # Asegurar que el costo siempre es positivo
        return max(0.1, final_cost)

    def find_shortest_path(self, start: tuple, end: tuple, courier: Courier = None, return_cost=False):
        """
        Encuentra la ruta más corta/óptima usando el algoritmo A*.
        """
        
        # CRÍTICO: 1. Verificación Inicial de Celdas
        # Si el inicio o el fin no son caminables, fallar inmediatamente.
        if not self.world.is_walkable(start[0], start[1]):
            if return_cost:
                return None, float('inf')
            return None
        if not self.world.is_walkable(end[0], end[1]):
            if return_cost:
                return None, float('inf')
            return None
            
        # Cola de prioridad: (costo_f, costo_g, posicion)
        open_list = [(0.0, 0.0, start)]
        
        # Mapeo de costo_g: costo real más barato encontrado hasta ahora para esa posición
        g_scores = {start: 0.0}
        
        # Mapeo para reconstruir la ruta: nodo_hijo: nodo_padre
        came_from = {}
        
        while open_list:
            # Extraer el nodo con el menor costo_f
            f_cost, g_cost, current_pos = heapq.heappop(open_list)
            
            # Si se llega al destino, reconstruir y retornar la ruta
            if current_pos == end:
                path = []
                temp = end
                while temp in came_from:
                    path.append(temp)
                    temp = came_from[temp]
                path.append(start)
                path.reverse()
                
                if return_cost:
                    return path, g_cost
                return path

            # Explorar vecinos
            for neighbor in self._get_neighbors(current_pos):
                
                # Calcular el costo real para ir a este vecino
                if courier:
                    # Usar la función de costo completa (maneja el peso, superficie, etc.)
                    move_cost = self.calculate_move_cost_for_courier(courier, current_pos, neighbor)
                else:
                    # Fallback: Costo base si no hay courier
                    move_cost = 1.0 / self.world.surface_weight_at(neighbor[0], neighbor[1]) 
                
                # CRÍTICO: Si el costo es infinito, ignorar este vecino.
                if move_cost == float('inf'):
                    continue
                
                # El nuevo costo_g es el costo_g actual más el costo de movimiento al vecino
                tentative_g_score = g_scores[current_pos] + move_cost

                # Si el vecino no ha sido visitado o encontramos un camino más barato
                if neighbor not in g_scores or tentative_g_score < g_scores[neighbor]:
                    
                    # 1. Actualizar el camino más barato encontrado
                    came_from[neighbor] = current_pos
                    g_scores[neighbor] = tentative_g_score
                    
                    # 2. Calcular el costo_f (costo_g + heurística)
                    h_score = manhattan_distance(neighbor, end)
                    f_score = tentative_g_score + h_score
                    
                    # 3. Agregar/Actualizar en la cola de prioridad
                    heapq.heappush(open_list, (f_score, tentative_g_score, neighbor)) 
                    
        # Si la lista abierta está vacía y no encontramos el objetivo
        if return_cost:
            return None, float('inf') # Retornar costo infinito si no hay ruta
        return None