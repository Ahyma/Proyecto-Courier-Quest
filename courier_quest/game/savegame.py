# src/savegame.py

"""
import pickle: para serializar y deserializar objetos de Python
import os: para manejar rutas de archivos y directorios
"""
import pickle, os


"""
Este bloque es para asegurarse de que el directorio de guardado exista y definir funciones para guardar y cargar el estado del juego

Primero definimos la ruta del directorio de guardado como una carpeta "saves" dentro del directorio padre del archivo actual
Luego, usamos os.makedirs para crear el directorio si no existe (exist_ok=True evita errores si ya existe)
Finalmente, definimos dos funciones:
- save_slot(filename, state_obj): guarda el objeto de estado serializado en un archivo dentro del directorio de guardado
- load_slot(filename): carga y retorna el objeto de estado deserializado desde un archivo dentro del directorio de guardado
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
