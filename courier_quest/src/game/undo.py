# courier_quest/src/game/undo.py
"""
from collections import deque es para manejar una pila con límite de tamaño
import copy es para hacer copias profundas del estado del juego
"""
from collections import deque
import copy

"""
UndoStack maneja una pila de estados del juego para permitir deshacer acciones

Primero define la clase UndoStack con un límite de tamaño (por defecto 20)
Luego tiene dos métodos principales:
- push: agrega una copia profunda del estado del juego a la pila, eliminando el estado más antiguo si se excede el límite
- pop: devuelve y elimina el estado más reciente de la pila, o None si la pila está vacía
"""
class UndoStack:
    def __init__(self, limit=20):
        self.limit = limit
        self.stack = deque()

    def push(self, game_state: dict):
        # copia profunda para no compartir referencias
        snap = copy.deepcopy(game_state)
        self.stack.append(snap)
        if len(self.stack) > self.limit:
            self.stack.popleft()

    def pop(self):
        if self.stack:
            return self.stack.pop()
        return None
