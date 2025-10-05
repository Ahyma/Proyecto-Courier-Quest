import pygame
from datetime import datetime, timedelta

class Job:
    """
    Representa un pedido individual en el juego.
    """
    def __init__(self, job_data, game_start_time):
        self.id = job_data.get('id', 'UNKNOWN')
        self.pickup_pos = tuple(job_data.get('pickup', [0, 0]))
        self.dropoff_pos = tuple(job_data.get('dropoff', [0, 0]))
        self.payout = job_data.get('payout', 0)
        self.weight = job_data.get('weight', 0)
        self.priority = job_data.get('priority', 0)
        self.release_time = job_data.get('release_time', 0)
        
        # Parsear deadline
        deadline_str = job_data.get('deadline', '')
        try:
            self.deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
        except:
            self.deadline = None
        
        # Estado del pedido
        self.state = "available"
        self.pickup_time = None
        self.delivery_time = None
        
        # Tiempo de juego
        self.game_start_time = game_start_time
        
    def is_available(self, current_game_time):
        """Verifica si el pedido está disponible según release_time"""
        return current_game_time >= self.release_time and self.state == "available"
    
    def pickup(self, current_game_time):
        """Marca el pedido como recogido"""
        if self.state == "available":
            self.state = "picked_up"
            self.pickup_time = current_game_time
            return True
        return False
    
    def deliver(self, current_game_time):
        """Marca el pedido como entregado"""
        if self.state == "picked_up":
            self.state = "delivered"
            self.delivery_time = current_game_time
            return True
        return False
    
    def cancel(self):
        """Cancela el pedido"""
        if self.state in ["available", "picked_up"]:
            self.state = "cancelled"
            return True
        return False
    
    def is_expired(self, current_game_time):
        """Verifica si el pedido ha expirado"""
        if not self.deadline or self.state != "available":
            return False
        
        current_dt = self.game_start_time + timedelta(seconds=current_game_time)
        return current_dt > self.deadline
    
    def get_time_until_deadline(self, current_game_time):
        """Retorna segundos restantes hasta deadline"""
        if not self.deadline:
            return float('inf')
        
        current_dt = self.game_start_time + timedelta(seconds=current_game_time)
        time_left = (self.deadline - current_dt).total_seconds()
        return max(0, time_left)
    
    def calculate_reputation_change(self):
        """Calcula cambio de reputación basado en tiempo de entrega"""
        if self.state != "delivered" or not self.delivery_time or not self.pickup_time:
            return 0
        
        delivery_duration = self.delivery_time - self.pickup_time
        estimated_duration = 120
        
        if delivery_duration <= estimated_duration * 0.8:
            return 5
        elif delivery_duration <= estimated_duration:
            return 3
        elif delivery_duration <= estimated_duration + 30:
            return -2
        elif delivery_duration <= estimated_duration + 120:
            return -5
        else:
            return -10
    
    def draw_markers(self, screen, TILE_SIZE, courier_pos):
        """Dibuja marcadores de pickup/dropoff si el pedido está activo"""
        if self.state == "picked_up":
            dropoff_rect = pygame.Rect(
                self.dropoff_pos[0] * TILE_SIZE,
                self.dropoff_pos[1] * TILE_SIZE,
                TILE_SIZE, TILE_SIZE
            )
            pygame.draw.rect(screen, (0, 255, 0), dropoff_rect, 2)
            
        elif self.state == "available" and self.is_close_to_pickup(courier_pos):
            pickup_rect = pygame.Rect(
                self.pickup_pos[0] * TILE_SIZE,
                self.pickup_pos[1] * TILE_SIZE,
                TILE_SIZE, TILE_SIZE
            )
            pygame.draw.rect(screen, (255, 255, 0), pickup_rect, 2)
    
    def is_close_to_pickup(self, courier_pos, distance=2):
        """Verifica si el courier está cerca del punto de pickup"""
        courier_x, courier_y = courier_pos
        pickup_x, pickup_y = self.pickup_pos
        return (abs(courier_x - pickup_x) <= distance and 
                abs(courier_y - pickup_y) <= distance)
    
    def is_at_pickup(self, courier_pos):
        """Verifica si el courier está lo suficientemente cerca del pickup"""
        courier_x, courier_y = courier_pos
        pickup_x, pickup_y = self.pickup_pos
        
        distance = abs(courier_x - pickup_x) + abs(courier_y - pickup_y)
        return distance <= 1
    
    def is_at_dropoff(self, courier_pos):
        """Verifica si el courier está lo suficientemente cerca del dropoff"""
        courier_x, courier_y = courier_pos
        dropoff_x, dropoff_y = self.dropoff_pos
        
        distance = abs(courier_x - dropoff_x) + abs(courier_y - dropoff_y)
        return distance <= 1
    
    def __str__(self):
        return f"Job {self.id} - {self.state} - ${self.payout} - {self.weight}kg"