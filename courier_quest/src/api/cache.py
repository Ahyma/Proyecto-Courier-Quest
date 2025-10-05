import json
import os

class APICache:
    def __init__(self, cache_dir="api_cache", data_dir="data"):
        self.cache_dir = cache_dir
        self.data_dir = data_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

    def save_data(self, filename, data):
        """Guarda datos en el directorio de caché."""
        path = os.path.join(self.cache_dir, filename)
        with open(path, 'w') as f:
            json.dump(data, f)
    
    def load_data(self, filename):
        """Intenta cargar datos desde la caché y luego desde el archivo local."""
        cache_path = os.path.join(self.cache_dir, filename)
        data_path = os.path.join(self.data_dir, filename)
        
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                return json.load(f)
        elif os.path.exists(data_path):
            with open(data_path, 'r') as f:
                return json.load(f)
        else:
            return None