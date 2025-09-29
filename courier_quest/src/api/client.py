# courier_quest/src/api/client.py
import requests
import json
from .cache import APICache

class APIClient:
    def __init__(self, api_cache):
        # URL base del API (sin /docs)
        self.base_url = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"
        self.api_cache = api_cache

    def _fetch_data(self, endpoint, local_file):
        """
        Intenta obtener datos del API y, si falla, los carga desde un archivo local.
        """
        url = f"{self.base_url}/city/{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            # Guardar en caché para futuras ejecuciones offline
            self.api_cache.save_data(local_file, data)
            print(f"Datos de {endpoint} cargados desde el API.")
            return data
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Fallo al conectar con el API: {e}. Intentando cargar desde caché...")
            return self.api_cache.load_data(local_file)

    def get_map_data(self):
        return self._fetch_data("map", "city.json")

    def get_jobs_data(self):
        return self._fetch_data("jobs", "jobs.json")
    
    def get_weather_data(self):
        return self._fetch_data("weather", "weather.json")
