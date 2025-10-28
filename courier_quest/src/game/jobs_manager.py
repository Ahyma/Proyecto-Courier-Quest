import pygame
import random
from datetime import datetime, timedelta
from .job import Job
from .inventory import Inventory


class JobsManager:
    """
    Gestor central de todos los pedidos del juego.
    
    Responsabilidades:
    - Carga inicial de pedidos desde JSON
    - Gestión del ciclo de vida de pedidos
    - Disponibilidad y expiración por tiempo
    - Coordinación de recogida y entrega
    - Generación de pedidos aleatorios
    """
    
    def __init__(self, jobs_data: dict, game_start_time: datetime | None = None):
        """
        Inicializa el gestor de pedidos.
        
        Args:
            jobs_data: Datos de pedidos desde JSON/API
            game_start_time: Hora de inicio del juego para cálculos temporales
        """
        self.game_start_time = game_start_time or datetime.now()
        self.all_jobs: list[Job] = self._load_jobs(jobs_data)  # Todos los pedidos
        self.available_jobs: list[Job] = []  # Pedidos disponibles para recoger
        self.completed_jobs: list[Job] = []  # Pedidos entregados exitosamente

    # ----------------------- CARGA -----------------------
    def _load_jobs(self, jobs_data: dict) -> list:
        """
        Carga pedidos desde datos, con manejo de errores.
        
        Returns:
            Lista de objetos Job cargados exitosamente
        """
        jobs: list[Job] = []
        for job_data in jobs_data.get("data", []):
            try:
                jobs.append(Job(job_data, self.game_start_time))
            except Exception as e:
                print(f"⚠️  Job inválido saltado: {e}")
        return jobs

    # --------------------- CICLO JUEGO -------------------
    def update(self, current_game_time: float, courier_pos: tuple[int, int]) -> None:
        """
        Actualiza el estado de todos los pedidos.
        
        Args:
            current_game_time: Tiempo actual del juego en segundos
            courier_pos: Posición actual del repartidor
        """
        # 1) Liberar jobs cuyo release_time ya pasó y aún no fueron tomados
        self.available_jobs = [
            j for j in self.all_jobs
            if j.state in ("pending", "available") and j.is_available(current_game_time)
               and not j.is_expired(current_game_time)
        ]
        
        # Actualizar estado de pending a available
        for j in self.available_jobs:
            if j.state == "pending":
                j.state = "available"

        # 2) Marcar pedidos expirados (incluye los en inventario)
        for j in self.all_jobs:
            if j.state in ("pending", "available", "picked_up") and j.is_expired(current_game_time):
                j.state = "expired"
                # Remover de disponibles si estaba ahí
                if j in self.available_jobs:
                    self.available_jobs.remove(j)

    # -------------------- BÚSQUEDAS ----------------------
    def get_available_jobs_nearby(self, courier_pos: tuple[int, int], max_distance: int = 3) -> list:
        """
        Encuentra pedidos disponibles cerca del repartidor.
        
        Returns:
            Lista de jobs dentro del rango especificado
        """
        return [j for j in self.available_jobs if j.is_close_to_pickup(courier_pos, max_distance)]

    # ----------------- Recoger / Entregar ----------------
    def try_pickup_job(
        self,
        job_id: str,
        courier_pos: tuple[int, int],
        inventory: Inventory,
        current_game_time: float
    ) -> bool:
        """
        Intenta recoger un pedido específico.
        
        Args:
            job_id: ID del pedido a recoger
            courier_pos: Posición actual del repartidor
            inventory: Inventario donde agregar el pedido
            current_game_time: Tiempo actual del juego
            
        Returns:
            True si se recogió exitosamente
        """
        for job in list(self.available_jobs):
            if job.id != job_id:
                continue  # No es el pedido buscado
                
            if not job.is_at_pickup(courier_pos):
                continue  # No está en posición de recogida
                
            if job.is_expired(current_game_time):
                job.state = "expired"
                self.available_jobs.remove(job)
                return False  # Pedido expirado
                
            if not inventory.can_add_job(job):
                return False  # Sin capacidad en inventario
                
            if job.pickup(current_game_time):
                inventory.add_job(job)
                self.available_jobs.remove(job)
                return True  # Recogida exitosa
                
        return False  # No se pudo recoger

    def try_deliver_job(
        self,
        inventory: Inventory,
        courier_pos: tuple[int, int],
        current_game_time: float
    ):
        """
        Intenta entregar el pedido actual del inventario.
        
        Args:
            inventory: Inventario con el pedido actual
            courier_pos: Posición actual del repartidor
            current_game_time: Tiempo actual del juego
            
        Returns:
            Job entregado o None si falló
        """
        current_job = inventory.current_job
        if not current_job:
            return None  # No hay pedido actual

        # Verificar si el pedido expiró en el inventario
        if current_job.is_expired(current_game_time):
            current_job.state = "expired"
            inventory.remove_current_job()
            return None

        # Verificar posición y entregar
        if current_job.is_at_dropoff(courier_pos) and current_job.deliver(current_game_time):
            delivered_job = inventory.remove_current_job()
            self.completed_jobs.append(delivered_job)
            return delivered_job

        return None

    # ----------------------- DIBUJO ----------------------
    def draw_job_markers(self, screen, TILE_SIZE: int, courier_pos: tuple[int, int]) -> None:
        """
        Dibuja marcadores visuales para pedidos en el mapa.
        
        - Amarillo: Puntos de recogida disponibles
        - Verde: Puntos de entrega para pedidos recogidos
        """
        # Pickups disponibles (amarillo)
        for job in self.available_jobs:
            if job.state == "available":
                px, py = job.pickup_pos
                pygame.draw.rect(
                    screen, (255, 255, 0),  # Amarillo
                    pygame.Rect(px * TILE_SIZE, py * TILE_SIZE, TILE_SIZE, TILE_SIZE), 2
                )

        # Dropoffs en curso (verde)
        for job in self.all_jobs:
            if job.state == "picked_up":
                dx, dy = job.dropoff_pos
                pygame.draw.rect(
                    screen, (0, 255, 0),  # Verde
                    pygame.Rect(dx * TILE_SIZE, dy * TILE_SIZE, TILE_SIZE, TILE_SIZE), 2
                )

    # ---------------------- ESTADOS ----------------------
    def get_stats(self) -> dict:
        """
        Obtiene estadísticas de todos los pedidos.
        
        Returns:
            Diccionario con conteos por estado
        """
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
        """Retorna la cantidad de pedidos disponibles."""
        return len(self.available_jobs)

    # --------------- GENERADOR DE PEDIDOS ----------------
    def generate_random_jobs(self, world, num_jobs: int = 15) -> None:
        """
        Genera pedidos aleatorios para cuando no hay datos externos.
        
        Args:
            world: Mundo del juego para obtener posiciones válidas
            num_jobs: Cantidad de pedidos a generar
        """
        building_edges = world.get_building_edges()  # Posiciones junto a edificios
        street_positions = world.get_street_positions()  # Posiciones en calles

        # Fallback si no hay bordes de edificios
        if not building_edges:
            print("❌ No hay bordes de edificios; usando calles como fallback.")
            building_edges = street_positions

        # Verificación crítica de posiciones válidas
        if not building_edges:
            print("❌❌ No hay posiciones válidas para generar pedidos.")
            return

        # Limpiar pedidos existentes
        self.all_jobs.clear()

        # Ajustar número real basado en posiciones disponibles
        actual_num = min(num_jobs, max(0, len(building_edges) - 1))
        if actual_num < num_jobs:
            print(f"⚠️  Reduciendo pedidos a {actual_num} (posiciones limitadas).")

        # Generar cada pedido
        for i in range(actual_num):
            pickup_pos = random.choice(building_edges)  # Posición de recogida aleatoria
            drop_candidates = [p for p in building_edges if p != pickup_pos]  # Evitar misma posición
            
            if not drop_candidates:
                continue  # No hay posiciones de entrega válidas
                
            dropoff_pos = random.choice(drop_candidates)  # Posición de entrega aleatoria

            # Configurar tiempos
            release_time = 0  # Disponible desde el comienzo
            deadline_dt = self.game_start_time + timedelta(seconds=random.randint(180, 420))  # 3-7 minutos

            # Crear datos del pedido
            job_data = {
                "id": f"PED-{i + 1:03d}",  # ID único
                "pickup": list(pickup_pos),
                "dropoff": list(dropoff_pos),
                "payout": random.randint(120, 400),  # Pago aleatorio
                "deadline": deadline_dt.isoformat(),  # Deadline en formato ISO
                "weight": random.randint(1, 3),  # Peso aleatorio
                "priority": random.randint(0, 2),  # Prioridad aleatoria
                "release_time": release_time,  # Disponibilidad inmediata
            }

            # Crear y agregar job
            job = Job(job_data, self.game_start_time)
            self.all_jobs.append(job)
            print(f"   📦 {job.id}: {pickup_pos} -> {dropoff_pos} | deadline {deadline_dt.time()}")

        print(f"✅ Generados {len(self.all_jobs)} pedidos.")