"""
import pickle es para serializar y deserializar objetos de Python
import os es para manejar rutas de archivos y directorios
"""
import pickle, os

"""
Este bloque configura el directorio donde se guardan las partidas, asegurándose de que exista

Primero define SAVE_DIR como una ruta relativa al directorio actual del archivo, apuntando a una carpeta "saves" un nivel arriba
Luego convierte SAVE_DIR a una ruta absoluta
Finalmente crea el directorio si no existe

Las funciones save_slot y load_slot permiten guardar y cargar el estado del juego en archivos dentro de SAVE_DIR
- save_slot: toma un nombre de archivo y un objeto de estado, y lo guarda en un archivo binario usando pickle
- load_slot: toma un nombre de archivo y carga el objeto de estado desde el archivo binario usando pickle
"""
SAVE_DIR = os.path.join(os.path.dirname(__file__), "..", "saves")
SAVE_DIR = os.path.abspath(SAVE_DIR)
os.makedirs(SAVE_DIR, exist_ok=True)

def save_slot(filename, state_obj):
    path = os.path.join(SAVE_DIR, filename)
    with open(path, "wb") as f:
        pickle.dump(state_obj, f, protocol=pickle.HIGHEST_PROTOCOL)

def load_slot(filename):
    path = os.path.join(SAVE_DIR, filename)
    with open(path, "rb") as f:
        return pickle.load(f)