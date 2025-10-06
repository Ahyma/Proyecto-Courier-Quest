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

## 6. Grafo (con dict de las listas de adyacencia)
- Ubicación: game/world.py
- Uso: Es lo que representa la ciudad como una red de nodos y calles (cada tile es un nodo), y así se facilita cálculos de rutas más cortas y validación de movimientos.
- Complejidad: Recorrido BFS/DFS: O(V + E), para la búsqueda de vecinos es O(1) promedio
- Justificación: Representación natural para mapas con conexiones bidireccionales y peso asociado.
- Explicación de O(V + E) proporcionada por chatGPT: Cuando hablamos de complejidad algorítmica, usamos la notación Big-O para describir cuánto tiempo tarda un algoritmo en función del tamaño del problema.
En un grafo, hay dos cosas que determinan su tamaño:
V → el número de vértices (o nodos)
→ En tu juego, serían las celdas del mapa (calles, parques, etc.)
E → el número de aristas (edges, conexiones entre nodos)
→ En el juego, serían las calles que conectan una celda con otra (por ejemplo, moverse de (2,3) a (2,4)).
La expresión O(V + E) significa que el tiempo total de ejecución del algoritmo depende linealmente del número de nodos y conexiones del grafo.

Es decir que si se duplica la cantidad de nodos o conexiones, el algortimo va a tardar el el doble aproximadamente. 

## 7. Archivos JSON y binarios
- Ubicación: game/score_board.py, game/save_game.py, api/cache.py
- Uso: Guardado de partidas (.sav binario), los puntajes (puntajes.json), y copias cacheadas del API (/api_cache/*.json)
- Justificación: Estos permiten persistencia de datos de usuario, récords y caché offline

## Complejidad algoritmica de las operaciones principales:

- Ordenar pedidos por prioridad: Se hizo con un Heap (heapq), tiene una complejidad de O(log n)
- Cambio de clima dinámico: Se hizo con cola FIFO (deque) + Cadena de Markov, tiene una complejidad de O(1) por actualización.
- Búsqueda de ruta en el mapa: Se hizo con BFS sobre grafo y la complejidad es de O(V + E).
- Deshacer movimiento: Se hizo con una pila, tiene una complejidad de O(1) y es lo que restaura el último estado del jugador.
- Carga desde API o caché: Se hizo con un diccionario, tiene una complejidad de O(1) en promedio, y es lo que busca datos cacheados antes de llamar al API.
- Gardar puntajes: Se hizo con un JSON, su complejidad algoritmica es de O(n log n), esto es lo que ordena puntajes descendentes antes de guardar. 

## Prompts utilizados 
I. Fundamentos y Conectividad (API y Estructura)
 * Estructura Base (Pygame):
   > "Dame el código de inicialización de Pygame para el proyecto, configurando el tamaño de la ventana y el bucle principal. Debo poder importar World y Courier."
   > 
 * API y Modo Offline:
   > "Implementa las clases APIClient y APICache. La lógica debe intentar obtener datos del API de la universidad (map, jobs, weather) y, si falla, cargar una copia local (/data/*.json), asegurando guardar la respuesta exitosa en el directorio de caché (/api_cache) para el uso sin conexión futuro."
   > 
 * Dimensiones Dinámicas:
   > "Ajusta la inicialización de Pygame para que las dimensiones de la pantalla (SCREEN_WIDTH, SCREEN_HEIGHT) se definan dinámicamente basándose en el width y height reales del mapa que retorna el API, multiplicados por TILE_SIZE."
   > 
II. Manejo del Mapa y Lógica de Terreno
 * Implementación de la clase World y Lógica de Terreno:
   > "Implementar la clase World para manejar el mapa del juego, incluyendo la lógica de carga de imágenes para edificios y calles, y definir métodos para verificar la transitabilidad (is_walkable) y el peso de superficie (surface_weight_at) de cada tile."
   > 
 * Agrupación de Edificios (BFS/DFS):
   > "En la clase World, implementa un método (get_building_size) que use un algoritmo de Búsqueda en Amplitud (BFS) o Profundidad (DFS) para detectar bloques contiguos de tiles de tipo 'B' (edificios), calcular sus dimensiones (WxH) y marcarlos como visitados. Luego, dibuja una única imagen para el bloque completo."
   > 
 * Texturizado del Mundo:
   > "Modifica la clase World para cargar imágenes de textura para calles (C), parques (P) y edificios (B) en lugar de colores sólidos. Asegúrate de que las imágenes se escalen correctamente a TILE_SIZE."
   > 
 * Métrica de Colisión:
   > "En la clase World, implementa el método is_walkable(x, y) para validar si el tile de destino (x, y) es transitable. Debe usar la matriz de tiles para asegurar que los edificios ('B') bloquean el paso."
   > 
 * Corrección sobre load_grass_image():
   > "Corregir una sugerencia previa, señalando que la función load_grass_image() no debe estar incluida en main.py si el código anterior funcionaba sin ella, y ajustando la inicialización de los componentes del juego para que el World reciba None como imagen de césped."
   > 
III. Lógica de Juego (Courier, Clima y Estado)
 * Desarrollo del Bucle Principal del Juego (incluyendo movimiento):
   > "Crear la estructura principal del juego en main.py, asegurando que el Courier (repartidor) pueda moverse por el mapa usando las teclas, respetando la lógica de transitabilidad de World y aplicando los modificadores de resistencia del clima."
   > 
 * Repartidor e Inventario:
   > "Crea la clase Courier. Debe manejar las estadísticas clave (stamina, money, reputation) y utilizar una estructura de datos lineal con límite (como una list o Queue) para gestionar el inventario de pedidos con las funciones pickup_job() y deliver_job()."
   > 
 * Cadenas de Markov (Clima):
   > "Diseña la clase WeatherManager que use la matriz de transición de Markov del archivo weather.json para gestionar el cambio de clima. Debe seleccionar el siguiente estado basado en probabilidades después de un burst_duration."
   > 
 * Costos de Movimiento Dinámico:
   > "Integra los datos de World.surface_weight_at(x, y) (peso del terreno) y el multiplicador de la condición climática de WeatherManager para calcular el costo de estamina. El método Courier.move() debe consumir Estamina = (Peso del Terreno \times Multiplicador de Clima)."
   > 
 * Interpolación Suave (Clima):
   > "Implementa la lógica de interpolación lineal en WeatherManager.get_speed_multiplier() y get_stamina_cost_multiplier() para que los cambios de un estado climático (ej. de 'Clear' a 'Storm') afecten las estadísticas del Courier de forma suave durante un transition_duration."
   > 
 * Implementación de Guardado y Carga de Partida:
   > "Implementar las funciones de guardar (save_slot) y cargar partida (load_slot) para preservar el estado del juego (posición del Courier, resistencia, estado del clima, etc.) y las clases de juego necesarias para manejarlo."
   > 
 * Condición de Fin de Juego:
   > "Añade la lógica de control en el bucle principal que detecte y maneje las condiciones de victoria y derrota, mostrando una pantalla final si el Courier alcanza el objetivo de dinero (goal del mapa) o si su Estamina llega a cero."
   > 
IV. Interfaz de Usuario (UI/UX) y Visuales
 * Adición del Menú Principal:
   > "Agregar un Menú Principal al inicio del juego con tres opciones: 'Nueva Partida', 'Cargar Partida' y 'Salir', y codificar la lógica para cambiar el estado del juego entre el menú y el juego en ejecución."
   > 
 * Definición del HUD y Panel Lateral:
   > "Definir una clase HUD y actualizar constants.py para incluir un panel lateral (PANEL_WIDTH) para mostrar información esencial del juego (resistencia, clima, velocidad), asegurando que el main.py dibuje el HUD correctamente a la derecha del mapa."
   > 
 * Heads-Up Display (HUD):
   > "Implementa un Heads-Up Display (HUD) en main.py para renderizar el estado del juego. Debe incluir barras de progreso para la Estamina y texto para el Dinero, Reputación y la Condición Climática actual."
   > 
 * Visuales del Clima:
   > "Crea la clase WeatherVisuals para que dibuje efectos gráficos (partículas de lluvia, capa de color para niebla, etc.) en la pantalla, sincronizándose con el estado actual y la intensidad proporcionada por el WeatherManager."
   > 
V. Recursos Gráficos (Efectos de Clima)
 * Partícula de Lluvia (Normal):
   > "Una pequeña imagen de una gota de lluvia inclinada, de color azul o gris claro. Debe tener un fondo transparente y ser lo suficientemente pequeña (por ejemplo, 5x10 píxeles) para que, al repetirse, simule la lluvia. En PNG porfavor, en efecto pixelArt"
   > 
 * Partícula de Tormenta:
   > "Una imagen de una gota de lluvia más grande y oscura que la de la lluvia normal. Puede tener un color azul oscuro o gris intenso para transmitir la sensación de una tormenta. En PNG y estilo pixelArt, con fondo transparente porfavor de 5x10 píxeles"
   > 
 * Partícula de Viento/Niebla:
   > "Una pequeña partícula alargada o una ráfaga de viento sutil. Un pequeño trazo de color gris con bordes suaves sería ideal. Debe tener un fondo transparente y orientarse horizontalmente. de 5x10 pixeles con efecto PixelArt porfavor"
   > 
 * Partícula de Nieve:
   > "Una imagen de un pequeño copo de nieve simple. Un diseño de estrella de seis puntas en color blanco sería perfecto. La transparencia del fondo es crucial. En png"
   > 
 * Partícula de Nube:
   > "Una imagen pequeña de una nube flotante con un fondo transparente. Debe tener un color celeste o gris claro. Esta imagen se moverá por la pantalla para simular el efecto. EN formato png y pixelArt porfavor"
 >
* Ayuda con depuración del main.py:
   > Incorporación del bucle principal (while running) con control de tiempo, condiciones de victoria y derrota.
    >
*Asistencia en la organización del HUD:
    > Para mostrar: tiempo restante, ingresos, reputación y estado del clima
  >
* Explicación lógica: 
   > Se pidió ayuda para entender la lógica del repartiddor (la velocidad, stamina, peso, reputación).
 >
 * Explicación técnica (O(1), lista de adyacencia, O(V+E)): 
   > Se pidieron aclaraciones conceptuales sobre complejidad amortizada, listas de adyacencia y la notación O(V + E). La IA explicó cada concepto con ejemplos aplicados al código del juego.
   >
 * Redacción de README con especificaciones dadas: 
   > Se pidió a la IA que nos ayudara a redactar un README con la información que le dimos acerca del proyecto una vez que lo completamos, y nos ayudó con la organización del mismo.
   >
