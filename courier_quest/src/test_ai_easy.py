# Headless test: define a minimal AICourier locally (to avoid importing main.py top-level deps)
import sys
import os
from enum import Enum
import random

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from game.courier import Courier


class AIDifficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3


class AICourier(Courier):
    def __init__(self, start_x, start_y, image, difficulty: AIDifficulty):
        super().__init__(start_x=start_x, start_y=start_y, image=image)
        self.difficulty = difficulty
        self.move_timer = 0.0
        self._target_job_id = None
        self._target_stage = None

    def _cooldown_for_difficulty(self) -> float:
        if self.difficulty == AIDifficulty.EASY:
            return 0.6
        if self.difficulty == AIDifficulty.HARD:
            return 0.20
        return 0.35

    def update(self, delta_time, game_world, weather_manager, jobs_manager=None, current_game_time: float = 0.0):
        self.move_timer -= delta_time
        if self.move_timer > 0:
            return
        self.move_timer = self._cooldown_for_difficulty()

        target_job = None
        if self._target_job_id and jobs_manager:
            for j in jobs_manager.all_jobs:
                if j.id == self._target_job_id:
                    target_job = j
                    break

        if not target_job and jobs_manager:
            available = [j for j in jobs_manager.available_jobs if j.state == 'available']
            if available:
                target_job = random.choice(available)
                if target_job:
                    self._target_job_id = target_job.id
                    self._target_stage = 'to_pickup'

        neighbors = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(neighbors)
        moved = False

        if target_job:
            dest = None
            if self._target_stage == 'to_pickup':
                dest = target_job.pickup_pos
            elif self._target_stage == 'to_dropoff':
                dest = target_job.dropoff_pos

            if dest:
                # EASY: greedy neighbor toward dest
                if self.difficulty == AIDifficulty.EASY:
                    best = None
                    best_dist = abs(self.x - dest[0]) + abs(self.y - dest[1])
                    for ndx, ndy in neighbors:
                        nx, ny = self.x + ndx, self.y + ndy
                        if not game_world.is_walkable(nx, ny):
                            continue
                        d = abs(nx - dest[0]) + abs(ny - dest[1])
                        if d < best_dist:
                            best_dist = d
                            best = (ndx, ndy)

                    if best:
                        dx, dy = best
                    else:
                        dx, dy = 0, 0

                else:
                    dx, dy = 0, 0

                if dx == 0 and dy == 0:
                    pass
                else:
                    new_x, new_y = self.x + dx, self.y + dy
                    stamina_cost_modifier = weather_manager.get_stamina_cost_multiplier()
                    climate_mult = weather_manager.get_speed_multiplier()
                    surface_weight = game_world.surface_weight_at(new_x, new_y)
                    self.move(dx, dy, stamina_cost_modifier=stamina_cost_modifier, surface_weight=surface_weight, climate_mult=climate_mult, game_world=game_world)
                    moved = True

        if not moved:
            for dx, dy in neighbors:
                new_x, new_y = self.x + dx, self.y + dy
                if not game_world.is_walkable(new_x, new_y):
                    continue
                stamina_cost_modifier = weather_manager.get_stamina_cost_multiplier()
                climate_mult = weather_manager.get_speed_multiplier()
                surface_weight = game_world.surface_weight_at(new_x, new_y)
                self.move(dx, dy, stamina_cost_modifier=stamina_cost_modifier, surface_weight=surface_weight, climate_mult=climate_mult, game_world=game_world)
                moved = True
                break


class DummyWorld:
    def is_walkable(self, x, y):
        return True
    def surface_weight_at(self, x, y):
        return 1.0


class DummyWeather:
    def get_current_condition(self):
        return 'clear'
    def get_stamina_cost_multiplier(self):
        return 1.0
    def get_speed_multiplier(self):
        return 1.0


class DummyJob:
    def __init__(self, id, pickup_pos, dropoff_pos):
        self.id = id
        self.pickup_pos = pickup_pos
        self.dropoff_pos = dropoff_pos
        self.state = 'available'


class DummyJobsManager:
    def __init__(self):
        self.all_jobs = []
        self.available_jobs = []


if __name__ == '__main__':
    world = DummyWorld()
    weather = DummyWeather()
    jobs = DummyJobsManager()

    # Add a job so AI has a target (this exercises the branch that previously left dx uninitialized)
    job = DummyJob(id='J1', pickup_pos=(7, 5), dropoff_pos=(10, 10))
    jobs.all_jobs.append(job)
    jobs.available_jobs.append(job)

    ai = AICourier(start_x=5, start_y=5, image=None, difficulty=AIDifficulty.EASY)

    try:
        # ensure AI will pick the job
        ai._target_job_id = job.id
        ai._target_stage = 'to_pickup'

        for i in range(8):
            ai.update(0.7, world, weather, jobs, current_game_time=0.0)
        print('OK: AICourier.update() ran without exception in EASY mode')
        print('AI final pos:', ai.x, ai.y)
    except Exception as e:
        print('ERROR: Exception during AICourier.update():', e)
        raise
