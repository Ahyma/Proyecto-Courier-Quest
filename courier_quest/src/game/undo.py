# courier_quest/src/game/undo.py
from collections import deque
import copy

class UndoStack:
    def __init__(self, limit=20):
        """
        Sistema de deshacer con límite de pasos.
        
        Args:
            limit (int): Máximo número de estados guardados
        """
        self.limit = limit
        self.stack = deque()
        print(f"✅ Sistema UNDO inicializado (límite: {limit} pasos)")

    def push(self, game_state: dict):
        """
        Guarda un estado del juego para poder deshacer.
        
        Args:
            game_state (dict): Estado completo del juego a guardar
        """
        # Copia profunda para no compartir referencias
        snap = copy.deepcopy(game_state)
        self.stack.append(snap)
        
        # Mantener solo los últimos 'limit' estados
        if len(self.stack) > self.limit:
            removed = self.stack.popleft()
            
        # Debug opcional
        # print(f"💾 Estado guardado en undo stack ({len(self.stack)}/{self.limit})")

    def pop(self):
        """
        Recupera el último estado guardado.
        
        Returns:
            dict or None: Último estado guardado, o None si no hay estados
        """
        if self.stack:
            state = self.stack.pop()
            # print(f"↩️  Estado recuperado del undo stack ({len(self.stack)} restantes)")
            return state
        else:
            return None

    def clear(self):
        """Limpia toda la historia de undo"""
        self.stack.clear()
        print("🧹 Undo stack limpiado")

    def get_stack_size(self):
        """Retorna cuántos estados hay guardados"""
        return len(self.stack)