""" 
from collections import deque es utilizado para manejar el inventario del courier, permitiendo una navegación eficiente y ordenamiento de los trabajos (jobs) en el inventario.
"""
from collections import deque

"""
Esta clase Inventory maneja el inventario del courier, permitiendo agregar, eliminar y navegar entre trabajos (jobs).
También soporta diferentes vistas de ordenamiento y permite aplicar un ordenamiento real basado en prioridad, fecha límite, pago o el orden original de inserción.
"""
class Inventory:
    """
    Maneja el inventario navegable del courier con diferentes vistas
    y permite aplicar ORDENAMIENTO REAL (F1–F4).
    """
    def __init__(self, max_weight):
        self.max_weight = max_weight
        self.jobs = deque()
        self.current_index = 0

        # Soporte para "orden original" (orden de inserción)
        self._insert_counter = 0
        self._last_sort_mode = None  # "priority" | "deadline" | "payout" | None

    # -------------------- helpers --------------------
    """
    Estos helpers son propiedades y métodos auxiliares para obtener el peso actual del inventario,
    el trabajo actual y para mantener el foco en el mismo trabajo después de operaciones de ordenamiento
    o eliminación
    """
    @property
    def current_weight(self):
        return sum(job.weight for job in self.jobs)

    @property
    def current_job(self):
        if self.jobs and 0 <= self.current_index < len(self.jobs):
            return self.jobs[self.current_index]
        return None

    """
    Este metodo mantiene el foco en el mismo trabajo (job) si existe; si no, establece el índice actual a 0
    """
    def _set_current_to(self, job_obj):
        """Mantiene el foco en el mismo job si existe; si no, index=0."""
        if not self.jobs:
            self.current_index = 0
            return
        if job_obj is None:
            self.current_index = 0
            return
        try:
            self.current_index = list(self.jobs).index(job_obj)
        except ValueError:
            self.current_index = 0

    # -------------------- mutadores --------------------
    """
    Estos métodos permiten agregar y eliminar trabajos (jobs) del inventario,
    así como navegar entre ellos (siguiente y anterior)

    can_add_job: Verifica si se puede agregar un trabajo sin exceder el peso máximo
    add_job: Agrega un trabajo al inventario si es posible
    remove_current_job: Elimina el trabajo actual del inventario
    next_job: Mueve el foco al siguiente trabajo en el inventario
    previous_job: Mueve el foco al trabajo anterior en el inventario
    """
    def can_add_job(self, job):
        return self.current_weight + job.weight <= self.max_weight

    def add_job(self, job):
        if self.can_add_job(job):
            # Marcar índice de inserción si no existe (para "orden original")
            if not hasattr(job, "_insert_seq"):
                job._insert_seq = self._insert_counter
                self._insert_counter += 1

            self.jobs.append(job)
            if len(self.jobs) == 1:
                self.current_index = 0
            return True
        return False

    def remove_current_job(self):
        if self.jobs and 0 <= self.current_index < len(self.jobs):
            removed_job = self.jobs[self.current_index]
            del self.jobs[self.current_index]

            if not self.jobs:
                self.current_index = 0
            elif self.current_index >= len(self.jobs):
                self.current_index = len(self.jobs) - 1

            return removed_job
        return None

    def next_job(self):
        if self.jobs:
            self.current_index = (self.current_index + 1) % len(self.jobs)
            return self.current_job
        return None

    def previous_job(self):
        if self.jobs:
            self.current_index = (self.current_index - 1) % len(self.jobs)
            return self.current_job
        return None

    # -------------------- vistas (para imprimir en consola si quieres) --------------------
    """ 
    Estos métodos devuelven listas de trabajos (jobs) ordenadas según diferentes criterios:
    get_jobs_sorted_by_priority: Ordena por prioridad (mayor a menor)
    get_jobs_sorted_by_deadline: Ordena por fecha límite (más cercana primero)
    get_jobs_sorted_by_payout: Ordena por pago (mayor a menor)
    get_jobs_sorted_by_distance: Ordena por distancia desde la posición del courier
    """ 
    def get_jobs_sorted_by_priority(self):
        return sorted(self.jobs, key=lambda job: (-job.priority, job.id))

    def get_jobs_sorted_by_deadline(self, current_game_time):
        return sorted(self.jobs, key=lambda job: (
            job.get_time_until_deadline(current_game_time)
            if getattr(job, "deadline", None) else float('inf')
        ))

    def get_jobs_sorted_by_payout(self):
        return sorted(self.jobs, key=lambda job: (-job.payout, job.id))

    def get_jobs_sorted_by_distance(self, courier_pos):
        return sorted(self.jobs, key=lambda job: (
            abs(courier_pos[0] - job.dropoff_pos[0]) +
            abs(courier_pos[1] - job.dropoff_pos[1])
        ))

    # -------------------- ORDENAMIENTO REAL --------------------
    """ 
    Este método reordena self.jobs EN SITIO según `mode` y mantiene el foco en el mismo job

    Primero verifica si hay trabajos en el inventario
    Luego guarda el trabajo actual para mantener el foco
    Dependiendo del modo, ordena la lista de trabajos según el criterio especificado
    """ 
    def apply_sort(self, mode, *, current_game_time=None):
        """
        Reordena self.jobs EN SITIO según `mode` y mantiene el foco en el mismo job.
        mode: "priority" | "deadline" | "payout" | "original"
        """
        if not self.jobs:
            return

        current = self.current_job  # conservar foco
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
                return float('inf')
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
    """ 
    Estos métodos proporcionan utilidades adicionales para el inventario:
    get_job_count: Devuelve el número de trabajos en el inventario
    is_empty: Indica si el inventario está vacío
    clear: Vacía el inventario
    """ 
    def get_job_count(self):
        return len(self.jobs)

    def is_empty(self):
        return len(self.jobs) == 0

    def clear(self):
        self.jobs.clear()
        self.current_index = 0
