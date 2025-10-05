from collections import deque

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
    @property
    def current_weight(self):
        return sum(job.weight for job in self.jobs)

    @property
    def current_job(self):
        if self.jobs and 0 <= self.current_index < len(self.jobs):
            return self.jobs[self.current_index]
        return None

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
    def get_job_count(self):
        return len(self.jobs)

    def is_empty(self):
        return len(self.jobs) == 0

    def clear(self):
        self.jobs.clear()
        self.current_index = 0
