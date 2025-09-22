
"""
import requests
import json
import os

#Definir la URL base de la API
API_BASE_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"
MAP_API_ENDPOINT = f"{API_BASE_URL}/city/map"
MAP_LOCAL_PATH = "data/map.json"

def get_map_data():
    
    Intenta obtener los datos del mapa de la API.
    Si falla, carga los datos del archivo local.
    
    try:
        print("Intentando obtener el mapa de la API...")
        response = requests.get(MAP_API_ENDPOINT)
        response.raise_for_status()
        
        # Si la solicitud fue exitosa, parsear el JSON
        map_data = response.json()
        print("Mapa obtenido de la API con éxito.")
        
        # Opcional: guardar una copia en caché para uso futuro
        os.makedirs(os.path.dirname(MAP_LOCAL_PATH), exist_ok=True)  # Crear directorio si no existe
        with open(MAP_LOCAL_PATH, 'w') as f:
            json.dump(map_data, f, indent=4)
        print("Mapa guardado en caché local.")
        
        return map_data
        
    except requests.exceptions.RequestException as e:
        print(f"No se pudo conectar a la API. Error: {e}")
        print("Cargando el mapa desde el archivo local...")
        
        # Intentar cargar desde el archivo local si existe
        if os.path.exists(MAP_LOCAL_PATH):
            with open(MAP_LOCAL_PATH, 'r') as f:
                map_data = json.load(f)
            print("Mapa cargado desde el archivo local con éxito.")
            return map_data
        else:
            print(f"Error: El archivo local '{MAP_LOCAL_PATH}' no existe.")
            return None


#=================================================================================================

def get_jobs_data():
    
    Intenta obtener los datos de los pedidos de la API.
    Si falla, carga los datos del archivo local.
    
    try:
        print("Intentando obtener los pedidos de la API...")
        response = requests.get(JOBS_API_ENDPOINT)
        response.raise_for_status()
        jobs_data = response.json()
        print("Pedidos obtenidos de la API con éxito.")

        with open(JOBS_LOCAL_PATH, 'w') as f:
            json.dump(jobs_data, f, indent=4)
        print("Pedidos guardados en caché local.")
        return jobs_data

    except requests.exceptions.RequestException as e:
        print(f"No se pudo conectar a la API. Error: {e}")
        print("Cargando los pedidos desde el archivo local...")
        if os.path.exists(JOBS_LOCAL_PATH):
            with open(JOBS_LOCAL_PATH, 'r') as f:
                jobs_data = json.load(f)
            print("Pedidos cargados desde el archivo local con éxito.")
            return jobs_data
        else:
            print(f"Error: El archivo local '{JOBS_LOCAL_PATH}' no existe.")
            return None

def get_weather_data():
    
    Intenta obtener los datos del clima de la API.
    Si falla, carga los datos del archivo local.
    
    try:
        print("Intentando obtener el clima de la API...")
        response = requests.get(WEATHER_API_ENDPOINT)
        response.raise_for_status()
        weather_data = response.json()
        print("Clima obtenido de la API con éxito.")

        with open(WEATHER_LOCAL_PATH, 'w') as f:
            json.dump(weather_data, f, indent=4)
        print("Clima guardado en caché local.")
        return weather_data

    except requests.exceptions.RequestException as e:
        print(f"No se pudo conectar a la API. Error: {e}")
        print("Cargando el clima desde el archivo local...")
        if os.path.exists(WEATHER_LOCAL_PATH):
            with open(WEATHER_LOCAL_PATH, 'r') as f:
                weather_data = json.load(f)
            print("Clima cargado desde el archivo local con éxito.")
            return weather_data
        else:
            print(f"Error: El archivo local '{WEATHER_LOCAL_PATH}' no existe.")
            return None"""

import requests
import json
import os

# Definir la URL base de la API
API_BASE_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"
MAP_API_ENDPOINT = f"{API_BASE_URL}/city/map"
JOBS_API_ENDPOINT = f"{API_BASE_URL}/city/jobs"
WEATHER_API_ENDPOINT = f"{API_BASE_URL}/city/weather"

# Rutas de los archivos locales para el modo offline
MAP_LOCAL_PATH = os.path.join("data", "map.json")
JOBS_LOCAL_PATH = os.path.join("data", "jobs.json")
WEATHER_LOCAL_PATH = os.path.join("data", "weather.json")

def get_map_data():
    """
    Intenta obtener los datos del mapa de la API.
    Si falla, carga los datos del archivo local.
    """
    try:
        print("Intentando obtener el mapa de la API...")
        response = requests.get(MAP_API_ENDPOINT)
        response.raise_for_status()
        
        # Si la solicitud fue exitosa, parsear el JSON
        map_data = response.json()
        print("Mapa obtenido de la API con éxito.")
        
        # Opcional: guardar una copia en caché para uso futuro
        os.makedirs(os.path.dirname(MAP_LOCAL_PATH), exist_ok=True)
        with open(MAP_LOCAL_PATH, 'w') as f:
            json.dump(map_data, f, indent=4)
        print("Mapa guardado en caché local.")
        
        return map_data
        
    except requests.exceptions.RequestException as e:
        print(f"No se pudo conectar a la API. Error: {e}")
        print("Cargando el mapa desde el archivo local...")
        
        # Intentar cargar desde el archivo local si existe
        if os.path.exists(MAP_LOCAL_PATH):
            with open(MAP_LOCAL_PATH, 'r') as f:
                map_data = json.load(f)
            print("Mapa cargado desde el archivo local con éxito.")
            return map_data
        else:
            print(f"Error: El archivo local '{MAP_LOCAL_PATH}' no existe.")
            return None


def get_jobs_data():
    """
    Intenta obtener los datos de los pedidos de la API.
    Si falla, carga los datos del archivo local.
    """
    try:
        print("Intentando obtener los pedidos de la API...")
        response = requests.get(JOBS_API_ENDPOINT)
        response.raise_for_status()
        jobs_data = response.json()
        print("Pedidos obtenidos de la API con éxito.")

        os.makedirs(os.path.dirname(JOBS_LOCAL_PATH), exist_ok=True)
        with open(JOBS_LOCAL_PATH, 'w') as f:
            json.dump(jobs_data, f, indent=4)
        print("Pedidos guardados en caché local.")
        return jobs_data

    except requests.exceptions.RequestException as e:
        print(f"No se pudo conectar a la API. Error: {e}")
        print("Cargando los pedidos desde el archivo local...")
        if os.path.exists(JOBS_LOCAL_PATH):
            with open(JOBS_LOCAL_PATH, 'r') as f:
                jobs_data = json.load(f)
            print("Pedidos cargados desde el archivo local con éxito.")
            return jobs_data
        else:
            print(f"Error: El archivo local '{JOBS_LOCAL_PATH}' no existe.")
            return None

def get_weather_data():
    """
    Intenta obtener los datos del clima de la API.
    Si falla, carga los datos del archivo local.
    """
    try:
        print("Intentando obtener el clima de la API...")
        response = requests.get(WEATHER_API_ENDPOINT)
        response.raise_for_status()
        weather_data = response.json()
        print("Clima obtenido de la API con éxito.")

        os.makedirs(os.path.dirname(WEATHER_LOCAL_PATH), exist_ok=True)
        with open(WEATHER_LOCAL_PATH, 'w') as f:
            json.dump(weather_data, f, indent=4)
        print("Clima guardado en caché local.")
        return weather_data

    except requests.exceptions.RequestException as e:
        print(f"No se pudo conectar a la API. Error: {e}")
        print("Cargando el clima desde el archivo local...")
        if os.path.exists(WEATHER_LOCAL_PATH):
            with open(WEATHER_LOCAL_PATH, 'r') as f:
                weather_data = json.load(f)
            print("Clima cargado desde el archivo local con éxito.")
            return weather_data
        else:
            print(f"Error: El archivo local '{WEATHER_LOCAL_PATH}' no existe.")
            return None
