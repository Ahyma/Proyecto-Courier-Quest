# courier_quest/src/game/undo.py
from collections import deque
import copy

class UndoStack:
    """
    Sistema de deshacer/rehacer para el juego.
    
    Guarda estados del juego para permitir deshacer acciones.
    Usa una cola de tamaño limitado para eficiencia de memoria.
    """
    
    def __init__(self, limit=20):
        """
        Inicializa el stack de deshacer.
        
        Args:
            limit (int): Máximo número de estados guardados
        """
        self.limit = limit
        self.stack = deque()  # Cola para almacenar estados
        print(f"✅ Sistema UNDO inicializado (límite: {limit} pasos)")

    def push(self, game_state: dict):
        """
        Guarda un estado del juego para poder deshacer.
        
        Args:
            game_state (dict): Estado completo del juego a guardar
        """
        # Copia profunda para evitar compartir referencias
        snap = copy.deepcopy(game_state)
        self.stack.append(snap)
        
        # Mantener solo los últimos 'limit' estados (FIFO)
        if len(self.stack) > self.limit:
            removed = self.stack.popleft()  # Eliminar estado más antiguo
            
        # Debug opcional
        # print(f"💾 Estado guardado en undo stack ({len(self.stack)}/{self.limit})")

    def pop(self):
        """
        Recupera el último estado guardado (deshacer).
        
        Returns:
            dict or None: Último estado guardado, o None si no hay estados
        """
        if self.stack:
            state = self.stack.pop()  # Obtener y eliminar último estado
            # print(f"↩️  Estado recuperado del undo stack ({len(self.stack)} restantes)")
            return state
        else:
            return None  # No hay estados para deshacer

    def clear(self):
        """Limpia toda la historia de undo (reinicia el stack)."""
        self.stack.clear()
        print("🧹 Undo stack limpiado")

    def get_stack_size(self):
        """Retorna cuántos estados hay guardados actualmente."""
        return len(self.stack)