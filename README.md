# Proyecto-Courier-Quest
Este proyecto consiste en el desarrollo de un videojuego en Python utilizando una librería de desarrollo de juegos. El juego, llamado Courier Quest, simula a un repartidor que debe aceptar y completar pedidos en una ciudad, gestionando tiempos de entrega, clima, inventario y prioridades.

# Estructuras de datos utilizadas 

## 1. Listas (list)
- Ubicación: game/world.py, game/inventory.py, game/wheather_manager.py
- Uso: Para almacenar los tiles del mapa y sus caracteristicas (world.tiles), mantener el inventario de pedidos aceptados por el jugador y para guardar las transiciones climáticas o ráfagas (bursts).
- Complejidad: En acceso por índice es O(1), en inserción/eliminación al final es O(1), finalmente en la inserción intermedia es de O(n). Con O(1) la operación se ejecuta en un tiempo que no depende del tamaño de la lista. 
- Justificación: Permiten recorrer y modificar fácilmente elementos secuenciales (tiles, clima, pedidos activos).

## 2. Diccionarios
- Ubicación: api/cache.py, game/world.py, game/constants.py
- Uso: Mapeo de claves del mapa (por ejemplo, "C" → "calle", "B" → "bloqueado"). El cacheo de datos descargados desde el API. Almacenamiento de configuraciones de juego y constantes.
- Complejidad: Con inserción, búsqueda y eliminación promedio: O(1) y en el peor caso (colisiones): O(n)
- Justificación: Las colecciones son ideales para accesos rápidos por clave (URLs, tipos de terreno, configuración del clima).

## 3. Cola FIFO (con collections.deque) 
- Ubicación: game/weather_manager.py, game/score_board.py
- Uso: Implementa la cola de ráfagas climáticas que se procesan en orden de llegada. La gestión de eventos secuenciales como animaciones o notificaciones en pantalla.
- Complejidad: Enqueue y dequeque: O(1), para el acceso aleatorio: O(n)
- Justificación: La cola permite manejar flujos ordenados (climas o eventos) con eficiencia y sin bloqueos.


## 4.  Pila (stack)
- Ubicación: game/save_game.py
- Uso: Implementa la función de “deshacer pasos” (undo) del jugador, cada acción (movimiento, entrega, cancelación) se apila para poder revertirla
- Complejidad: Push y pop: O(1), acceso al tope: O(1)
- Justificación: LIFO es ideal para revertir acciones recientes sin recorrer todo el historial.

## 5.  Cola de prioridad (heapq)
- Ubicación: game/inventory.py, game/world.py
- Uso: Ordena los pedidos activos según prioridad o tiempo de entrega, y se usa para seleccionar el siguiente pedido más urgente.
- Complejidad: Inserción y extracción mínima: O(log n), para búsqueda directa: O(n)
- Justificación: Permite manejar prioridades de entrega de forma eficiente, mejorando el rendimiento del juego.

6. Grafo
7. Archivos JSON y binarios

## Complejidad algoritmica:
- 
