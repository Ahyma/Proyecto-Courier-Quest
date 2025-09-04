
"""
import pygame

class Courier:
    def _init_(self, start_x, start_y, max_stamina=100, max_speed=5):
        
        Inicializa una nueva instancia de la clase Courier.
        Args:
            start_x (int): La posición inicial X en la cuadrícula del mapa.
            start_y (int): La posición inicial Y en la cuadrícula del mapa.
            max_stamina (int): La resistencia máxima del repartidor.
            max_speed (int): La velocidad máxima del repartidor.
        
        # Posición y movimiento
        self.x = start_x
        self.y = start_y
        self.speed = max_speed

        # Estadísticas del personaje
        self.stamina = max_stamina
        self.max_stamina = max_stamina
        self.money = 0
        self.reputation = 0
        
        # Inventario de pedidos
        # Se usa una lista como inventario para guardar los pedidos.
        self.inventory = []
        
    def move(self, dx, dy):
        
        Actualiza la posición del repartidor en la cuadrícula.
        
        Args:
            dx (int): El cambio en la posición X (ej. -1, 0, 1).
            dy (int): El cambio en la posición Y (ej. -1, 0, 1).
        
        # Mueve al repartidor
        self.x += dx
        self.y += dy
        
        # Reduce la resistencia con cada movimiento
        self.stamina -= 1

    def pickup_job(self, job):
        
        Añade un pedido al inventario del repartidor.
        
        Args:
            job (dict): Un diccionario que representa el pedido a recoger.
        
        if len(self.inventory) < 3: # Asume un límite de inventario de 3
            self.inventory.append(job)
            print(f"Pedido {job.get('id')} recogido en ({self.x}, {self.y}).")
        else:
            print("Inventario lleno. No se puede recoger más pedidos.")

    def deliver_job(self):
        
        Entrega el primer pedido del inventario y actualiza las estadísticas.
        
        Returns:
            dict: El pedido entregado o None si el inventario está vacío.
        
        if self.inventory:
            # Elimina el primer pedido (comportamiento de cola/FIFO)
            job = self.inventory.pop(0) 
            self.money += job.get('reward', 0)
            self.reputation += job.get('reputation', 0)
            print(f"Pedido {job.get('id')} entregado. Ganaste ${job.get('reward', 0)} y {job.get('reputation', 0)} de reputación.")
            return job
        else:
            print("No hay pedidos para entregar.")
            return None

    def gain_stamina(self, amount):
        
        Aumenta la resistencia del repartidor.
        
        Args:
            amount (int): La cantidad de resistencia a ganar.
        
        self.stamina = min(self.stamina + amount, self.max_stamina)
        
    def draw(self, screen, TILE_SIZE):
        
        Dibuja al repartidor en la pantalla.
        
        Args:
            screen (pygame.Surface): La superficie de la pantalla de Pygame.
            TILE_SIZE (int): El tamaño en píxeles de cada tile.
        
        # Posición en píxeles
        pos_x = self.x * TILE_SIZE + TILE_SIZE // 2
        pos_y = self.y * TILE_SIZE + TILE_SIZE // 2
        
        # Dibujar un círculo rojo para representar al repartidor
        pygame.draw.circle(screen, (255, 0, 0), (pos_x, pos_y), TILE_SIZE // 2)"""

import pygame

class Courier:
    def __init__(self, start_x, start_y, image, max_stamina=100, max_speed=5):
        """
        Inicializa una nueva instancia de la clase Courier.
        
        Args:
            start_x (int): La posición inicial X en la cuadrícula del mapa.
            start_y (int): La posición inicial Y en la cuadrícula del mapa.
            image (pygame.Surface): La imagen del repartidor.
            max_stamina (int): La resistencia máxima del repartidor.
            max_speed (int): La velocidad máxima del repartidor.
        """
        # Posición y movimiento
        self.x = start_x
        self.y = start_y
        self.speed = max_speed
        self.image = image # Guarda la imagen para dibujarla
        self.rect = self.image.get_rect() # Obtiene el rectángulo para la posición

        # Estadísticas del personaje
        self.stamina = max_stamina
        self.max_stamina = max_stamina
        self.money = 0
        self.reputation = 0
        
        # Inventario de pedidos
        self.inventory = []
        
    def move(self, dx, dy):
        """
        Actualiza la posición del repartidor en la cuadrícula.
        
        Args:
            dx (int): El cambio en la posición X (ej. -1, 0, 1).
            dy (int): El cambio en la posición Y (ej. -1, 0, 1).
        """
        # Mueve al repartidor
        self.x += dx
        self.y += dy
        
        # Reduce la resistencia con cada movimiento
        self.stamina -= 1

    def pickup_job(self, job):
        """
        Añade un pedido al inventario del repartidor.
        """
        if len(self.inventory) < 3: # Asume un límite de inventario de 3
            self.inventory.append(job)
            print(f"Pedido {job.get('id')} recogido en ({self.x}, {self.y}).")
        else:
            print("Inventario lleno. No se puede recoger más pedidos.")

    def deliver_job(self):
        """
        Entrega el primer pedido del inventario y actualiza las estadísticas.
        """
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
        """
        Aumenta la resistencia del repartidor.
        """
        self.stamina = min(self.stamina + amount, self.max_stamina)
        
    def draw(self, screen, TILE_SIZE):
        """
        Dibuja al repartidor en la pantalla usando su imagen.
        """
        # Actualiza el rectángulo de la imagen a la posición del repartidor
        self.rect.topleft = (self.x * TILE_SIZE, self.y * TILE_SIZE)
        
        # Dibuja la imagen en la pantalla
        screen.blit(self.image, self.rect)

