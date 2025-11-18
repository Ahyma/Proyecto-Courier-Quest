# Proyecto-Courier-Quest 

Courier Quest es un videojuego desarrollado en Python que simula la experiencia de un repartidor en una ciudad dinámica.  
El objetivo del jugador (o de la IA) es aceptar y completar pedidos, gestionando:

- rutas óptimas,
- clima dinámico,
- estamina,
- peso del inventario,
- reputación,
- tiempos de entrega,
- y prioridades de pedidos.

En la **parte 2 del proyecto**, se incorporó un sistema avanzado de **Inteligencia Artificial**, pathfinding A*, heurísticas, efectos visuales del clima, HUD completo, guardado/carga de partidas y un sistema de puntajes.

---

# Inteligencia Artificial Implementada

El proyecto incluye **tres niveles de IA**, cada uno con comportamientos y algoritmos más sofisticados:

## 1. IA EASY
- Movimiento “greedy” hacia pickup o dropoff.  
- Evita devolverse sobre la casilla anterior.  
- Timeout para evitar ciclos y estancamiento.  
- No usa A*, ni heurísticas complejas.

## 2. IA MEDIUM
- Lookahead mediante DFS (profundidad 3).  
- Función heurística con pesos:


- Considera clima, peso, distancia, prioridad y estamina.  
- Penalización a casillas visitadas recientemente (evita bucles).  
- Reevaluación estratégica del job cuando pierde sentido mantenerlo.

## 3. IA HARD
- Pathfinding **A\*** con pesos según tipo de terreno (`surface_weight`).  
- Replanificación dinámica (clima, estamina baja, cambio de job).  
- Selección de pedidos mediante **cola de prioridad (heapq)** usando una heurística **TSP-like** que estima el valor de encadenar múltiples pedidos.  
- Considera costo real del terreno, clima y rutas completas.

---

# Clima y Efectos Visuales

El sistema climático usa:

- **Cadena de Markov** para transiciones probabilísticas.  
- **Cola FIFO (deque)** para manejar ráfagas o eventos climáticos.  
- **Interpolación suave** para cambios progresivos en velocidad y estamina.  
- **WeatherVisuals** para lluvia, tormenta, viento, nubes, nieve, niebla y calor.

El clima afecta:

- velocidad del courier (speed multiplier),  
- consumo de estamina (stamina multiplier),  
- decisiones de IA MEDIUM y HARD.

---

# Guardado, Carga y Puntajes

### Guardado/Carga
Se almacena:
- posición del courier,  
- estado del clima,  
- estamina, ingresos, reputación, inventario,  
- tiempo de juego,  
- jobs aceptados y pendientes.

Implementado mediante archivos **binarios (.sav)**.

### Puntajes
Se guardan en JSON e incluyen:
- puntaje total,  
- ingresos,  
- tiempo en partida,  
- reputación final.

---

# HUD e Interfaz

Incluye:
- barra de estamina,  
- estado climático,  
- ingresos,  
- reputación,  
- peso del inventario,  
- job actual,  
- tiempo de juego.

El HUD fue actualizado para soportar:
- visualización de dificultad de IA,  
- colores diferenciados,  
- depuración visual del pathfinding (ruta de la IA HARD).

---

# Estructuras de Datos Utilizadas

## 1. Listas (`list`)
**Ubicación:** world.py, inventory.py, weather_manager.py  
**Uso:**  
- tiles del mapa (`world.tiles`),  
- inventario de pedidos,  
- partículas del clima,  
- historial de posiciones recientes de la IA.  
**Complejidad:** acceso O(1), inserción intermedia O(n)  
**Justificación:** estructura secuencial flexible para elementos contiguos.

---

## 2. Diccionarios (`dict`)
**Ubicación:** api/cache.py, world.py, constants.py  
**Uso:**  
- leyenda del mapa,  
- pesos de terreno,  
- configuración del clima,  
- caché de llamadas al API.  
**Complejidad:** O(1) promedio  
**Justificación:** accesos rápidos por clave.

---

## 3. Cola FIFO (`collections.deque`)
**Ubicación:** weather_manager.py, score_board.py  
**Uso:**  
- ráfagas climáticas,  
- eventos secuenciales del juego,  
- estadísticas del análisis técnico de la IA.  
**Complejidad:** O(1) enqueue/dequeue.

---

## 4. Pila (stack)
**Ubicación:** save_game.py  
**Uso:**  
- sistema de “undo” (deshacer acciones del jugador).  
**Complejidad:** push/pop O(1).  
**Justificación:** LIFO ideal para revertir el estado reciente.

---

## 5. Cola de prioridad (`heapq`)
**Ubicación:** ai_courier.py (IA HARD), inventory.py  
**Uso:**  
- selección óptima de pedidos,  
- ordenamiento por prioridad o score.  
**Complejidad:** O(log n).  
**Justificación:** permite siempre obtener el elemento de mayor valor con eficiencia.

---

## 6. Grafo implícito (lista de adyacencia conceptual)
**Ubicación:** world.py  
**Uso:**  
- representación del mapa como un grid,  
- vecinos cardinales (arriba/abajo/izquierda/derecha),  
- soporte a pathfinding A*.  
**Complejidad:**  
- BFS/DFS: O(V + E)  
- A*: O(E log V)  
**Justificación:** el mapa se comporta naturalmente como un grafo.

---

## 7. Archivos JSON y Binarios
**Ubicación:** score_board.py, save_game.py, api/cache.py  
**Uso:**  
- guardado de puntajes,  
- almacenamiento de partida,  
- cache local del API.  
**Justificación:** persistencia del juego y soporte fuera de línea.

---

# Complejidad Algorítmica de Operaciones Principales

| Operación | Algoritmo | Complejidad |
|----------|-----------|-------------|
| Ordenar pedidos por prioridad | heapq | O(log n) |
| Cambio dinámico de clima | deque + Markov | O(1) por actualización |
| Pathfinding | A* con pesos | O(E log V) |
| Lookahead IA MEDIUM | DFS profundidad 3 | O(b³) |
| Detección de edificios contiguos | BFS | O(V + E) |
| Undo (deshacer) | stack | O(1) |
| Carga desde API o caché | dict | O(1) |
| Guardar puntajes | ordenamiento JSON | O(n log n) |

---

# Uso de IA

Se consultó a la IA múltiples veces para:

- depuración de clases (`main.py`, `world.py`, `hud.py`)  
- corrección de errores 
- guia y explicación de implementación   
- implementación del pathfinding A*  
- diseño de ciertos aspectos del HUD y pantalla lateral  
- redacción del readme y diseño del readme (por ejemplo: tabla, formato, redacción clara)
  
# Propmts Utilizados
- “Me esta dando este error cuando el ai_courier retira un pedido:
AttributeError: 'JobsManager' object has no attribute 'try_deliver_current_job'”
- “El nivel medio se bugea en la posicion 25,12… busquemos una solución que respete el enunciado.”
- “Puedes indicarme de la lista qué está solucionado y qué falta?”
- “Aca esta lo que necesito que me ayudes a hacer
  IA MEDIA — componentes técnicos
Lookahead completo de 2–3 movimientos.
Ajuste fino de los valores α, β, γ, δ, ε del score.
Minimizar o crear una versión simple de minimax / expectimax.
  IA DIFÍCIL — núcleo avanzado
Implementar A dinámico real (replanificación completa).
Generar rutas múltiples (TSP aproximado).
Integrar colas de prioridad para seleccionar el siguiente job.
  Competitividad general de la IA
Ajustar heurísticas para que la IA sea realmente competitiva.
  Análisis técnico
Evaluación formal del rendimiento de la IA (tiempos, eficiencia, comparaciones).”
- "Analiza la arquitectura completa del proyecto Courier Quest y dime cómo extenderla para agregar un jugador CPU competitivo sin romper el código existente."
- "Valida si la clase AICourier está correctamente integrada con Courier y qué mejoras necesita para soportar heurísticas avanzadas."
- "Explícame cómo gestionar la barra de estamina, reputación e ingresos de la IA de forma equivalente al jugador humano."
- "Diseña un flujo completo de decisiones para la IA: seleccionar pedido, planear ruta, moverse, recoger, entregar y reevaluar."
- "Enséñame cómo implementar un random walk evitando edificios para la IA Fácil."
- "Haz que la IA Fácil elija un job disponible al azar respetando su capacidad de carga."
- "Ayúdame a configurar un timeout interno que reinicie el objetivo si la IA queda atrapada."
- "Explica cómo detectar estancamientos cuando la IA no avanza hacia su destino."
- "Explícame cómo implementar una heurística que combine payout, distancia y clima para decidir movimientos de IA Media."
- "Diseña la función score = αpayout – βdistancia – γ*penalización_clima y muestra cómo aplicarla."
- "Enséñame a generar un lookahead corto de 2–3 movimientos para mejorar la IA Media sin usar minimax completo."
- "Explícame cómo convertir la ciudad en un grafo para que la IA Difícil use pathfinding."
- "Ayúdame a implementar A* para que la IA Difícil encuentre rutas óptimas según clima y superficie."
- "Explícame cómo replanificar rutas cuando: cambia el clima, baja la estamina o se bloquea un camino."
- "Enséñame cómo usar colas de prioridad (heapq) para expandir nodos en A*."
- "Ayúdame a crear un HUD que muestre datos del jugador y de la IA: ingresos, reputación, stamina y entregas."
- "Enséñame a dibujar la ruta estimada de la IA en el mapa usando líneas y puntos en Pygame."
- "Quiero un toggle de debug (F5) que muestre u oculte la ruta planificada por la IA."
- "Genera un indicador visual en el HUD que muestre si la IA está en timeout o estancada."
- "Agrega un panel comparativo (Jugador vs IA) que muestre: ingresos, reputación y entregas realizadas."
- "Con respecto al error, mejor dime exactamente que clases necesitas ver y así yo te las envio por aquí, para que tengas acceso explicito a ellas"
- "Este es el readme actual. Actualizalo con todo aquello que agregamos en esta segunda parte del proyecto. Y dame el readme listo y actualizado con toda la información que te di en el mensaje anterior. Hazlo muy ordenado, limpio y bonito. De ser posible incluye tablas y divisiones."

---
