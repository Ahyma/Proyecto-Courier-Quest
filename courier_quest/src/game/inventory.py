from collections import deque
from datetime import datetime

class Inventory:
    """
    Maneja el inventario navegable del courier con diferentes vistas.
    """
    def __init__(self, max_weight):
        self.max_weight = max_weight
        self.jobs = deque()
        self.current_index = 0
        
    @property
    def current_weight(self):
        return sum(job.weight for job in self.jobs)
    
    @property
    def current_job(self):
        if self.jobs and 0 <= self.current_index < len(self.jobs):
            return self.jobs[self.current_index]
        return None
    
    def can_add_job(self, job):
        return self.current_weight + job.weight <= self.max_weight
    
    def add_job(self, job):
        if self.can_add_job(job):
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
    
    def get_jobs_sorted_by_priority(self):
        return sorted(self.jobs, key=lambda job: (-job.priority, job.id))
    
    def get_jobs_sorted_by_deadline(self, current_game_time):
        return sorted(self.jobs, key=lambda job: (
            job.get_time_until_deadline(current_game_time) 
            if job.deadline else float('inf')
        ))
    
    def get_jobs_sorted_by_payout(self):
        return sorted(self.jobs, key=lambda job: (-job.payout, job.id))
    
    def get_jobs_sorted_by_distance(self, courier_pos):
        return sorted(self.jobs, key=lambda job: (
            abs(courier_pos[0] - job.dropoff_pos[0]) + 
            abs(courier_pos[1] - job.dropoff_pos[1])
        ))
    
    def get_job_count(self):
        return len(self.jobs)
    
    def is_empty(self):
        return len(self.jobs) == 0
    
    def clear(self):
        self.jobs.clear()
        self.current_index = 0