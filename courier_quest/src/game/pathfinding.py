"""
A* pathfinding para la cuadrícula del juego.
Retorna una lista de posiciones (x, y) desde la posición siguiente hasta el objetivo inclusive,
ó `None` si no existe camino.

La función tiene en cuenta el peso de la superficie (`world.surface_weight_at`) y un factor
dependiente del clima (`weather_manager.get_speed_multiplier()`), de forma que rutas sobre
superficies pesadas o con clima adverso resulten en un coste mayor.
"""
from heapq import heappush, heappop
from typing import Optional, Tuple, List

"""
manhattan calcula la distancia Manhattan entre dos puntos
La distancia Manhattan es la suma de las diferencias absolutas de sus coordenadas
Es decir, para dos puntos a=(x1,y1) y b=(x2,y2), la distancia Manhattan es |x1 - x2| + |y1 - y2|
"""
def manhattan(a: Tuple[int,int], b: Tuple[int,int]) -> int:
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def find_path(start: Tuple[int,int], goal: Tuple[int,int], world, weather_manager, courier=None, max_nodes: int = 10000) -> Optional[List[Tuple[int,int]]]:
    """
    Calcula un camino usando A* entre dos posiciones en la cuadrícula.

    ----------------Parameters---------------
    start : tuple[int, int]
        Posición inicial del courier expresada como (x, y) en coordenadas de tile
    goal : tuple[int, int]
        Posición objetivo (x, y) 
    world :
        Objeto que expone al menos:
          - is_walkable(x: int, y: int) -> bool
          - surface_weight_at(x: int, y: int) -> float
    weather_manager :
        Objeto que expone get_speed_multiplier() -> float. Es para
        ajustar el coste de movimiento según el clima actual.
    courier : Courier | None, opcional
        Si se proporciona, se usa su estado de stamina para penalizar
        rutas largas cuando la resistencia es baja.
    max_nodes : int
        Límite de nodos expandidos para evitar que A* consuma demasiados
        recursos en mapas grandes o sin solución.

    --------------Returns-----------
    list[tuple[int, int]] | None
        Lista de posiciones (x, y) que representan el camino desde el
        primer paso después de `start` hasta `goal` inclusive. Si no se
        encuentra camino, retorna None.
    """
    if start == goal:
        return []

    speed_mult = max(0.1, weather_manager.get_speed_multiplier())

    open_heap = []
    heappush(open_heap, (0 + manhattan(start, goal), 0, start))  # (f, g, node)
    came_from = {start: None}
    gscore = {start: 0}

    nodes_expanded = 0

    while open_heap:
        f, g, current = heappop(open_heap)
        nodes_expanded += 1
        if nodes_expanded > max_nodes:
            break

        if current == goal:
            # reconstruct path
            path = []
            cur = current
            while cur and cur != start:
                path.append(cur)
                cur = came_from.get(cur)
            path.reverse()
            return path

        x, y = current
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x + dx, y + dy
            if not world.is_walkable(nx, ny):
                continue
            # cost to move into (nx,ny)
            surface = world.surface_weight_at(nx, ny)
            """
            base cost = surface_weight * inverse of speed: (worse speed => more cost)
            calles "pesadas" => surface_weight > 1 => más costosas
            clima adverso => speed_mult < 1 => más costoso
            """
            move_cost = surface * (1.0 / speed_mult)
            # small penalty if courier is low on stamina (prefer shorter routes)
            if courier is not None:
                if hasattr(courier, 'stamina') and hasattr(courier, 'max_stamina'):
                    sta_pct = max(0.0, min(1.0, courier.stamina / max(1, courier.max_stamina)))
                    # if very low stamina, slightly penalize longer moves
                    if sta_pct < 0.3:
                        move_cost *= 1.25

            tentative_g = g + move_cost
            neigh = (nx, ny)
            if tentative_g < gscore.get(neigh, float('inf')):
                gscore[neigh] = tentative_g
                priority = tentative_g + manhattan(neigh, goal)
                came_from[neigh] = current
                heappush(open_heap, (priority, tentative_g, neigh))

    return None
