""" 
import pygame es para representar un gestor de trabajos (jobs) en el juego Courier Quest
import random es para generar trabajos aleatorios
from datetime import datetime, timedelta es para manejar tiempos y fechas, como deadlines y release times
from .job import Job importa la clase Job del módulo job
from .inventory import Inventory importa la clase Inventory del módulo inventory
""" 
import pygame
import random
from datetime import datetime, timedelta
from .job import Job
from .inventory import Inventory


class JobsManager:
    """
    Gestiona todos los pedidos del juego:
      - Carga inicial desde JSON
      - Disponibilidad por release_time
      - Expiración por deadline
      - Recogida/entrega y transición de estados
      - Estadísticas y utilidades de dibujo
    """
    def __init__(self, jobs_data: dict, game_start_time: datetime | None = None):
        self.game_start_time = game_start_time or datetime.now()
        self.all_jobs: list[Job] = self._load_jobs(jobs_data)
        self.available_jobs: list[Job] = []
        self.completed_jobs: list[Job] = []

    # ----------------------- CARGA -----------------------
    """ 
    _load_jobs: Carga trabajos desde jobs_data y maneja errores
    """ 
    def _load_jobs(self, jobs_data: dict) -> list:
        jobs: list[Job] = []
        for job_data in jobs_data.get("data", []):
            try:
                jobs.append(Job(job_data, self.game_start_time))
            except Exception as e:
                print(f"Job inválido saltado: {e}")
        return jobs

    # --------------------- CICLO JUEGO -------------------
    """ 
    update: Refresca la disponibilidad y expiración de trabajos según el tiempo actual
    """ 
    def update(self, current_game_time: float, courier_pos: tuple[int, int]) -> None:
        """
        Refresca:
          - cuáles están disponibles (release_time cumplido)
          - cuáles han expirado (deadline)
        """
        # 1) Liberar jobs cuyo release_time ya pasó y aún no fueron tomados
        self.available_jobs = [
            j for j in self.all_jobs
            if j.state in ("pending", "available") and j.is_available(current_game_time)
               and not j.is_expired(current_game_time)
        ]
        for j in self.available_jobs:
            if j.state == "pending":
                j.state = "available"

        # 2) Marcar expirados (incluye los en inventario)
        for j in self.all_jobs:
            if j.state in ("pending", "available", "picked_up") and j.is_expired(current_game_time):
                j.state = "expired"
                if j in self.available_jobs:
                    self.available_jobs.remove(j)

    # -------------------- BÚSQUEDAS ----------------------
    """ 
    get_available_jobs_nearby: Devuelve trabajos disponibles cerca de la posición del courier
    """ 
    def get_available_jobs_nearby(self, courier_pos: tuple[int, int], max_distance: int = 3) -> list:
        return [j for j in self.available_jobs if j.is_close_to_pickup(courier_pos, max_distance)]

    # ----------------- Recoger / Entregar ----------------
    """ 
    try_pickup_job: Intenta recoger un trabajo si el courier está en el punto de recogida y el trabajo está disponible
    """ 
    def try_pickup_job(
        self,
        job_id: str,
        courier_pos: tuple[int, int],
        inventory: Inventory,
        current_game_time: float
    ) -> bool:
        for job in list(self.available_jobs):
            if job.id != job_id:
                continue
            if not job.is_at_pickup(courier_pos):
                continue
            if job.is_expired(current_game_time):
                job.state = "expired"
                self.available_jobs.remove(job)
                return False
            if not inventory.can_add_job(job):
                return False
            if job.pickup(current_game_time):
                inventory.add_job(job)
                self.available_jobs.remove(job)
                return True
        return False

    def try_deliver_job(
        self,
        inventory: Inventory,
        courier_pos: tuple[int, int],
        current_game_time: float
    ):
        """
        Entrega el pedido seleccionado si corresponde.
        Devuelve el Job entregado o None.
        (El cálculo de reputación lo hace job.calculate_reputation_change()
         que tu main ya llama después de cobrar.)
        """
        current_job = inventory.current_job
        if not current_job:
            return None

        if current_job.is_expired(current_game_time):
            current_job.state = "expired"
            inventory.remove_current_job()
            return None

        if current_job.is_at_dropoff(courier_pos) and current_job.deliver(current_game_time):
            delivered_job = inventory.remove_current_job()
            self.completed_jobs.append(delivered_job)
            return delivered_job

        return None

    # ----------------------- DIBUJO ----------------------
    """ 
    draw_job_markers: Dibuja marcadores en la pantalla para los trabajos según su estado y la posición del courier

    Primero dibuja los pickups disponibles en amarillo y luego los dropoffs en curso en verde
    Luego, para cada trabajo:
    - Si está "picked_up", dibuja un rectángulo verde en la posición de entrega (dropoff)
    - Si está "available" o "pending" y el courier está cerca del punto de recogida (pickup), dibuja un rectángulo amarillo en la posición de recogida (pickup)
    """ 
    def draw_job_markers(self, screen, TILE_SIZE: int, courier_pos: tuple[int, int]) -> None:
        # Pickups disponibles (amarillo)
        for job in self.available_jobs:
            if job.state == "available":
                px, py = job.pickup_pos
                pygame.draw.rect(
                    screen, (255, 255, 0),
                    pygame.Rect(px * TILE_SIZE, py * TILE_SIZE, TILE_SIZE, TILE_SIZE), 2
                )

        # Dropoffs en curso (verde)
        for job in self.all_jobs:
            if job.state == "picked_up":
                dx, dy = job.dropoff_pos
                pygame.draw.rect(
                    screen, (0, 255, 0),
                    pygame.Rect(dx * TILE_SIZE, dy * TILE_SIZE, TILE_SIZE, TILE_SIZE), 2
                )

    # ---------------------- ESTADOS ----------------------
    """ 
    get_stats: Devuelve estadísticas de trabajos como total, disponibles, completados, en progreso y expirados
    get_available_jobs_count: Devuelve la cantidad de trabajos disponibles actualmente
    """ 
    def get_stats(self) -> dict:
        total = len(self.all_jobs)
        available = len(self.available_jobs)
        completed = sum(1 for j in self.all_jobs if j.state == "delivered")
        in_progress = sum(1 for j in self.all_jobs if j.state == "picked_up")
        expired = sum(1 for j in self.all_jobs if j.state == "expired")
        return {
            "total": total,
            "available": available,
            "completed": completed,
            "in_progress": in_progress,
            "expired": expired,
        }

    def get_available_jobs_count(self) -> int:
        return len(self.available_jobs)

    # --------------- GENERADOR DE PEDIDOS ----------------
    """ 
    generate_random_jobs: Genera trabajos aleatorios basados en los bordes de edificios del mundo

    Primero obtiene las posiciones de los bordes de edificios y calles
    Luego, para el número solicitado de trabajos:
    - Selecciona aleatoriamente una posición de recogida (pickup)
    - Selecciona aleatoriamente una posición de entrega (dropoff) diferente
    - Asigna un release_time de 0 (disponible desde el inicio)
    - Asigna un deadline aleatorio entre 3 y 7 minutos desde el inicio del juego
    - Asigna un pago (payout) aleatorio entre 120 y 400
    - Asigna un peso (weight) aleatorio entre 1 y 3
    - Asigna una prioridad aleatoria entre 0 y 2 
    Finalmente, agrega el trabajo generado a self.all_jobs
    """ 
    def generate_random_jobs(self, world, num_jobs: int = 15) -> None:
        building_edges = world.get_building_edges()
        street_positions = world.get_street_positions()

        if not building_edges:
            print("No hay bordes de edificios; usando calles como fallback.")
            building_edges = street_positions

        if not building_edges:
            print("No hay posiciones válidas para generar pedidos.")
            return

        self.all_jobs.clear()

        actual_num = min(num_jobs, max(0, len(building_edges) - 1))
        if actual_num < num_jobs:
            print(f"Reduciendo pedidos a {actual_num} (posiciones limitadas).")

        for i in range(actual_num):
            pickup_pos = random.choice(building_edges)
            drop_candidates = [p for p in building_edges if p != pickup_pos]
            if not drop_candidates:
                continue
            dropoff_pos = random.choice(drop_candidates)

            release_time = 0  # disponibles desde el comienzo
            deadline_dt = self.game_start_time + timedelta(seconds=random.randint(180, 420))

            job_data = {
                "id": f"PED-{i + 1:03d}",
                "pickup": list(pickup_pos),
                "dropoff": list(dropoff_pos),
                "payout": random.randint(120, 400),
                "deadline": deadline_dt.isoformat(),
                "weight": random.randint(1, 3),
                "priority": random.randint(0, 2),
                "release_time": release_time,
            }

            job = Job(job_data, self.game_start_time)
            self.all_jobs.append(job)
            print(f"  {job.id}: {pickup_pos} -> {dropoff_pos} | deadline {deadline_dt.time()}")

        print(f"Generados {len(self.all_jobs)} pedidos.")
