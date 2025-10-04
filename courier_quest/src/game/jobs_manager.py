import pygame
from datetime import datetime, timedelta
import random
from .job import Job
from .inventory import Inventory

class JobsManager:
    """
    Gestiona todos los pedidos del juego: disponibles, en progreso, y completados.
    """
    def __init__(self, jobs_data, game_start_time=None):
        self.game_start_time = game_start_time or datetime.now()
        self.all_jobs = self._load_jobs(jobs_data)
        self.available_jobs = []
        self.completed_jobs = []
        
    def _load_jobs(self, jobs_data):
        jobs = []
        jobs_list = jobs_data.get('data', [])
        
        for job_data in jobs_list:
            job = Job(job_data, self.game_start_time)
            jobs.append(job)
            
        return jobs
    
    def update(self, current_game_time, courier_pos):
        self.available_jobs = [job for job in self.all_jobs 
                              if job.is_available(current_game_time)]
        
        for job in self.available_jobs[:]:
            if job.is_expired(current_game_time):
                job.state = "expired"
                self.available_jobs.remove(job)
    
    def get_available_jobs_nearby(self, courier_pos, max_distance=3):
        nearby_jobs = []
        for job in self.available_jobs:
            if job.is_close_to_pickup(courier_pos, max_distance):
                nearby_jobs.append(job)
        return nearby_jobs
    
    def try_pickup_job(self, job_id, courier_pos, inventory, current_game_time):
        for job in self.available_jobs:
            if job.id == job_id and job.is_at_pickup(courier_pos):
                if inventory.can_add_job(job) and job.pickup(current_game_time):
                    inventory.add_job(job)
                    self.available_jobs.remove(job)
                    return True
        return False
    
    def try_deliver_job(self, inventory, courier_pos, current_game_time):
        current_job = inventory.current_job
        if current_job and current_job.is_at_dropoff(courier_pos):
            if current_job.deliver(current_game_time):
                delivered_job = inventory.remove_current_job()
                self.completed_jobs.append(delivered_job)
                return delivered_job
        return None
    
    def draw_job_markers(self, screen, TILE_SIZE, courier_pos):
        for job in self.available_jobs:
            if job.state == "available":
                pickup_rect = pygame.Rect(
                    job.pickup_pos[0] * TILE_SIZE,
                    job.pickup_pos[1] * TILE_SIZE,
                    TILE_SIZE, TILE_SIZE
                )
                pygame.draw.rect(screen, (255, 255, 0), pickup_rect, 2)

        for job in self.all_jobs:
            if job.state == "picked_up":
                dropoff_rect = pygame.Rect(
                    job.dropoff_pos[0] * TILE_SIZE,
                    job.dropoff_pos[1] * TILE_SIZE,
                    TILE_SIZE, TILE_SIZE
                )
                pygame.draw.rect(screen, (0, 255, 0), dropoff_rect, 2)
    
    def get_stats(self):
        total = len(self.all_jobs)
        available = len(self.available_jobs)
        completed = len([j for j in self.all_jobs if j.state == "delivered"])
        in_progress = len([j for j in self.all_jobs if j.state == "picked_up"])
        expired = len([j for j in self.all_jobs if j.state == "expired"])
        
        return {
            "total": total,
            "available": available,
            "completed": completed,
            "in_progress": in_progress,
            "expired": expired
        }

    def generate_random_jobs(self, world, num_jobs=15):
        """
        Genera pedidos aleatorios - TODOS disponibles inmediatamente
        """
        building_edges = world.get_building_edges()
        street_positions = world.get_street_positions()
        
        if not building_edges:
            print("❌ No hay bordes de edificios para generar pedidos")
            # Usar calles como fallback
            building_edges = street_positions
        
        if not building_edges:
            print("❌❌ No hay posiciones válidas para generar pedidos")
            return
        
        self.all_jobs = []
        
        print(f"📍 Bordes de edificios disponibles: {len(building_edges)}")
        
        # Limitar el número de pedidos al número de posiciones disponibles
        actual_num_jobs = min(num_jobs, len(building_edges) - 1)
        if actual_num_jobs < num_jobs:
            print(f"⚠️  Reduciendo pedidos a {actual_num_jobs} (no hay suficientes posiciones)")
        
        for i in range(actual_num_jobs):
            # Elegir pickup y dropoff diferentes
            pickup_pos = random.choice(building_edges)
            
            # Asegurar que dropoff sea diferente y esté disponible
            possible_dropoffs = [pos for pos in building_edges if pos != pickup_pos]
            if not possible_dropoffs:
                print(f"⚠️  No hay dropoff disponible para {pickup_pos}, saltando pedido")
                continue
                
            dropoff_pos = random.choice(possible_dropoffs)
            
            # TODOS los pedidos disponibles inmediatamente (release_time = 0)
            job_data = {
                "id": f"PED-{i+1:03d}",
                "pickup": list(pickup_pos),
                "dropoff": list(dropoff_pos),
                "payout": random.randint(100, 400),
                "deadline": "2025-09-01T12:30:00",
                "weight": random.randint(1, 3),
                "priority": random.randint(0, 2),
                "release_time": 0  # ¡IMPORTANTE! Todos disponibles desde el inicio
            }
            
            job = Job(job_data, self.game_start_time)
            self.all_jobs.append(job)
            print(f"   📦 Pedido {job.id} en {pickup_pos} -> {dropoff_pos}")
        
        print(f"✅ Generados {len(self.all_jobs)} pedidos disponibles inmediatamente")

    def get_available_jobs_count(self):
        return len(self.available_jobs)