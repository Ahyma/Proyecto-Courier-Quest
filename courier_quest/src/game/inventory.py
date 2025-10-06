from collections import deque

class Inventory:
    """
    Sistema de inventario navegable para el repartidor.
    
    Características:
    - Capacidad limitada por peso
    - Navegación entre pedidos
    - Ordenamiento en tiempo real (F1-F4)
    - Diferentes vistas del inventario
    """
    
    def __init__(self, max_weight):
        """
        Inicializa el inventario.
        
        Args:
            max_weight: Peso máximo que puede cargar el inventario
        """
        self.max_weight = max_weight
        self.jobs = deque()  # Cola de pedidos (double-ended queue)
        self.current_index = 0  # Índice del pedido actualmente seleccionado

        # Soporte para orden original (orden de inserción)
        self._insert_counter = 0  # Contador para orden de inserción
        self._last_sort_mode = None  # Último modo de ordenamiento usado

    # -------------------- helpers --------------------
    @property
    def current_weight(self):
        """Calcula el peso total actual del inventario."""
        return sum(job.weight for job in self.jobs)

    @property
    def current_job(self):
        """Retorna el pedido actualmente seleccionado."""
        if self.jobs and 0 <= self.current_index < len(self.jobs):
            return self.jobs[self.current_index]
        return None

    def _set_current_to(self, job_obj):
        """
        Mantiene el foco en el mismo job si existe.
        
        Args:
            job_obj: El job que debería ser el actual
        """
        if not self.jobs:
            self.current_index = 0
            return
        if job_obj is None:
            self.current_index = 0
            return
        try:
            # Buscar índice del job en la lista
            self.current_index = list(self.jobs).index(job_obj)
        except ValueError:
            # Si no se encuentra, usar primer job
            self.current_index = 0

    # -------------------- mutadores --------------------
    def can_add_job(self, job):
        """Verifica si se puede agregar un job sin exceder el peso máximo."""
        return self.current_weight + job.weight <= self.max_weight

    def add_job(self, job):
        """
        Agrega un job al inventario si hay capacidad.
        
        Returns:
            True si se agregó exitosamente, False si no
        """
        if self.can_add_job(job):
            # Marcar índice de inserción para orden original
            if not hasattr(job, "_insert_seq"):
                job._insert_seq = self._insert_counter
                self._insert_counter += 1

            self.jobs.append(job)
            # Si es el primer job, seleccionarlo automáticamente
            if len(self.jobs) == 1:
                self.current_index = 0
            return True
        return False

    def remove_current_job(self):
        """
        Elimina el job actualmente seleccionado.
        
        Returns:
            El job eliminado o None si no hay jobs
        """
        if self.jobs and 0 <= self.current_index < len(self.jobs):
            removed_job = self.jobs[self.current_index]
            del self.jobs[self.current_index]

            # Ajustar índice actual después de eliminar
            if not self.jobs:
                self.current_index = 0  # Sin jobs
            elif self.current_index >= len(self.jobs):
                self.current_index = len(self.jobs) - 1  # Último job

            return removed_job
        return None

    def next_job(self):
        """Selecciona el siguiente job en el inventario (círculo)."""
        if self.jobs:
            self.current_index = (self.current_index + 1) % len(self.jobs)
            return self.current_job
        return None

    def previous_job(self):
        """Selecciona el job anterior en el inventario (círculo)."""
        if self.jobs:
            self.current_index = (self.current_index - 1) % len(self.jobs)
            return self.current_job
        return None

    # -------------------- vistas (para imprimir en consola si quieres) --------------------
    def get_jobs_sorted_by_priority(self):
        """Retorna lista de jobs ordenados por prioridad (descendente)."""
        return sorted(self.jobs, key=lambda job: (-job.priority, job.id))

    def get_jobs_sorted_by_deadline(self, current_game_time):
        """Retorna lista de jobs ordenados por tiempo hasta deadline."""
        return sorted(self.jobs, key=lambda job: (
            job.get_time_until_deadline(current_game_time)
            if getattr(job, "deadline", None) else float('inf')
        ))

    def get_jobs_sorted_by_payout(self):
        """Retorna lista de jobs ordenados por pago (descendente)."""
        return sorted(self.jobs, key=lambda job: (-job.payout, job.id))

    def get_jobs_sorted_by_distance(self, courier_pos):
        """Retorna lista de jobs ordenados por distancia al repartidor."""
        return sorted(self.jobs, key=lambda job: (
            abs(courier_pos[0] - job.dropoff_pos[0]) +
            abs(courier_pos[1] - job.dropoff_pos[1])
        ))

    # -------------------- ORDENAMIENTO REAL --------------------
    def apply_sort(self, mode, *, current_game_time=None):
        """
        Reordena el inventario según el modo especificado.
        
        Args:
            mode: "priority" | "deadline" | "payout" | "original"
            current_game_time: Tiempo actual del juego (necesario para deadline)
        """
        if not self.jobs:
            return

        current = self.current_job  # Conservar job actual para restaurar foco
        lst = list(self.jobs)

        if mode == "priority":
            lst.sort(key=lambda job: (-job.priority, job.id))
            self._last_sort_mode = "priority"

        elif mode == "deadline":
            if current_game_time is None:
                return
            def key_deadline(job):
                if getattr(job, "deadline", None):
                    return job.get_time_until_deadline(current_game_time)
                return float('inf')  # Jobs sin deadline van al final
            lst.sort(key=key_deadline)
            self._last_sort_mode = "deadline"

        elif mode == "payout":
            lst.sort(key=lambda job: (-job.payout, job.id))
            self._last_sort_mode = "payout"

        elif mode == "original":
            lst.sort(key=lambda job: getattr(job, "_insert_seq", 0))
            self._last_sort_mode = None

        # Reescribir la deque y restaurar foco
        self.jobs.clear()
        self.jobs.extend(lst)
        self._set_current_to(current)

    # -------------------- utilidades --------------------
    def get_job_count(self):
        """Retorna la cantidad de jobs en el inventario."""
        return len(self.jobs)

    def is_empty(self):
        """Verifica si el inventario está vacío."""
        return len(self.jobs) == 0

    def clear(self):
        """Limpia todo el inventario."""
        self.jobs.clear()
        self.current_index = 0