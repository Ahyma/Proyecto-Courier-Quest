import pygame
import os

class Courier:
    def __init__(self, start_x, start_y, image, max_stamina=100, max_speed=5):
        self.x = start_x
        self.y = start_y
        self.speed = max_speed
        self.stamina = max_stamina
        self.max_stamina = max_stamina
        self.money = 0
        self.reputation = 0
        self.inventory = []
        self.image = image
        
    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        self.stamina -= 1

    def pickup_job(self, job):
        if len(self.inventory) < 3:
            self.inventory.append(job)
            print(f"Pedido {job.get('id')} recogido en ({self.x}, {self.y}).")
        else:
            print("Inventario lleno. No se puede recoger más pedidos.")

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
        else:
            # Si no hay imagen, dibuja un círculo para depuración
            pos_x = self.x * TILE_SIZE + TILE_SIZE // 2
            pos_y = self.y * TILE_SIZE + TILE_SIZE // 2
            pygame.draw.circle(screen, (255, 0, 0), (pos_x, pos_y), TILE_SIZE // 2)