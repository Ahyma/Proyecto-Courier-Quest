import pygame
import os

class Courier:
    def __init__(self, start_x, start_y, image, max_stamina=100, max_speed=5, max_weight=5):
        self.x = start_x
        self.y = start_y
        self.speed = max_speed
        self.stamina = max_stamina
        self.max_stamina = max_stamina
        self.money = 0
        self.reputation = 0
        self.max_weight = max_weight # Peso máximo que puede llevar
        self.inventory = [] 
        self.image = image
        self.packages_delivered = 0 # Contador de pedidos entregados
        
    @property
    def current_weight(self):
        """Calcula el peso total de los pedidos en el inventario.
        Asume que cada pedido tiene una clave 'weight'."""
        total_weight = sum(job.get('weight', 0) for job in self.inventory)
        return total_weight

    def move(self, dx, dy, stamina_cost_multiplier=1.0):
        # Lógica de penalización de peso (un ejemplo simple)
        base_stamina_cost = 1 
        weight_penalty = self.current_weight * 0.1 # 10% más de costo por cada unidad de peso
        total_stamina_cost = (base_stamina_cost + weight_penalty) * stamina_cost_multiplier
        
        self.x += dx
        self.y += dy
        # El costo de resistencia total se calcula con el multiplicador de clima y la penalización de peso
        self.stamina = max(0, self.stamina - total_stamina_cost) 

    def pickup_job(self, job):
        job_weight = job.get('weight', 0)
        
        # Verifica el límite de peso. Puedes añadir tu propia lógica de límite de ítems si es necesario.
        if self.current_weight + job_weight <= self.max_weight:
            self.inventory.append(job)
            print(f"Pedido {job.get('id')} recogido en ({self.x}, {self.y}). Peso: {job_weight}.")
        else:
            print(f"Inventario lleno o excedería el peso máximo de {self.max_weight} (Peso actual: {self.current_weight}).")

    def deliver_job(self):
        if self.inventory:
            job = self.inventory.pop(0)
            self.money += job.get('reward', 0)
            self.reputation += job.get('reputation', 0)
            print(f"Pedido {job.get('id')} entregado. Ganaste ${job.get('reward', 0)} y {job.get('reputation', 0)} de reputación.")
            return job
        else:
            print("No hay pedidos para entregar.")
            return None

    def gain_stamina(self, amount):
        self.stamina = min(self.stamina + amount, self.max_stamina)

    def draw(self, screen, TILE_SIZE):
        if self.image:
            # Dibuja la imagen del repartidor en la posición actual
            screen.blit(self.image, (self.x * TILE_SIZE, self.y * TILE_SIZE))