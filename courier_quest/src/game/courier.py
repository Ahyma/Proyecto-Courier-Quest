"""import pygame
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
    
        #Calcula el peso total de los pedidos en el inventario.
        #Asume que cada pedido tiene una clave 'weight'.
       
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
"""

import pygame

class Courier:
    def __init__(self, start_x, start_y, image,
                 max_stamina=100, base_speed=3.0, max_weight=10):
        self.x = start_x
        self.y = start_y
        self.image = image

        # Atributos básicos
        self.base_speed = base_speed      # v0 en el enunciado
        self.stamina = max_stamina
        self.max_stamina = max_stamina
        self.income = 0                   # dinero ganado
        self.reputation = 70              # inicia en 70 según enunciado
        self.max_weight = max_weight
        self.inventory = []
        self.packages_delivered = 0

    # -----------------------
    # --- PROPIEDADES ---
    # -----------------------
    @property
    def current_weight(self):
        """Peso total de los pedidos en el inventario."""
        return sum(job.get('weight', 0) for job in self.inventory)

    @property
    def stamina_state(self):
        """Retorna el estado de resistencia (normal, cansado, exhausto)."""
        if self.stamina <= 0:
            return "exhausto"
        elif self.stamina <= 30:
            return "cansado"
        else:
            return "normal"

    # -----------------------
    # --- MOVIMIENTO ---
    # -----------------------
    def move(self, dx, dy, stamina_cost_modifier=1.0, surface_weight=1.0,
             climate_mult=1.0):
        """
        Aplica el movimiento con fórmula completa del enunciado.
        Args:
            dx, dy: dirección (-1,0,1)
            stamina_cost_modifier: penalizador extra del clima
            surface_weight: multiplicador de tile (ej. parque = 0.95)
            climate_mult: multiplicador de velocidad por clima
        """

        # --- Multiplicadores ---
        # Mpeso: mínimo 0.8
        Mpeso = max(0.8, 1 - 0.03 * self.current_weight)

        # Mrep: +3% si reputación >= 90
        Mrep = 1.03 if self.reputation >= 90 else 1.0

        # Mresistencia según estado
        if self.stamina <= 0:
            Mresistencia = 0.0
        elif self.stamina <= 30:
            Mresistencia = 0.8
        else:
            Mresistencia = 1.0

        # Velocidad final
        final_speed = (self.base_speed * climate_mult *
                       Mpeso * Mrep * Mresistencia * surface_weight)

        # Si está exhausto, no se mueve
        if Mresistencia == 0:
            return

        # Mover (1 casilla por tecla presionada, pero con idea de escala)
        self.x += dx
        self.y += dy

        # --- Consumo de stamina ---
        base_stamina_cost = 0.5  # por celda
        # penalización extra por peso (>3)
        extra_weight_penalty = 0.2 * max(0, self.current_weight - 3)
        total_cost = (base_stamina_cost + extra_weight_penalty) * stamina_cost_modifier
        self.stamina = max(0, self.stamina - total_cost)

    # -----------------------
    # --- INVENTARIO ---
    # -----------------------
    def pickup_job(self, job):
        job_weight = job.get('weight', 0)
        if self.current_weight + job_weight <= self.max_weight:
            self.inventory.append(job)
            print(f"Pedido {job.get('id')} recogido. Peso: {job_weight}.")
        else:
            print(f"Inventario lleno: no puedes cargar {job_weight} extra.")

    def deliver_job(self):
        if self.inventory:
            job = self.inventory.pop(0)
            payout = job.get('payout', 0)
            self.income += payout
            # reputación se ajustará según reglas en otra parte
            self.packages_delivered += 1
            print(f"Pedido {job.get('id')} entregado. Ganaste ${payout}.")
            return job
        else:
            print("No hay pedidos para entregar.")
            return None

    # -----------------------
    # --- RESISTENCIA ---
    # -----------------------
    def gain_stamina(self, amount):
        self.stamina = min(self.stamina + amount, self.max_stamina)

    # -----------------------
    # --- DIBUJO ---
    # -----------------------
    def draw(self, screen, TILE_SIZE):
        if self.image:
            screen.blit(self.image, (self.x * TILE_SIZE, self.y * TILE_SIZE))

"""
ahora se usa income en lugar de money para empatar con el enunciado.

Reputación inicia en 70.

Movimiento ahora considera peso, reputación, resistencia, clima y surface_weight.

Maneja estados de resistencia (normal, cansado, exhausto).

Penalización de stamina basada en reglas del enunciado.
"""