# courier_quest/src/game/undo.py
from collections import deque
import copy

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
