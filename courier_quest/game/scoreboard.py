# src/scoreboard.py
"""
import json: para manejar archivos JSON
import os: para manejar rutas de archivos y directorios
"""
import json, os


"""
Este bloque es para asegurarse de que el directorio de datos exista y definir funciones para cargar y guardar puntajes

Primero definimos la ruta del directorio de datos como una carpeta "data" dentro del directorio padre del archivo actual
Luego, usamos os.makedirs para crear el directorio si no existe (exist_ok=True evita errores si ya existe)
Finalmente, definimos dos funciones:
- load_scores(): carga y retorna la lista de puntajes desde un archivo JSON dentro del directorio de datos (retorna lista vacía si no existe o hay error)
- save_score(entry): agrega una nueva entrada de puntaje a la lista, la ordena y la guarda de nuevo en el archivo JSON
"""
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DATA_DIR = os.path.abspath(DATA_DIR)
PATH = os.path.join(DATA_DIR, "puntajes.json")

"""Funciones para cargar y guardar puntajes"""
def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_scores():
    _ensure_dir()
    if os.path.exists(PATH):
        try:
            with open(PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_score(entry):
    scores = load_scores()
    scores.append(entry)
    scores.sort(key=lambda s: s.get("score",0), reverse=True)
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)
