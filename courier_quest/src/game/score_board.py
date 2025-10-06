# courier_quest/src/game/score_board.py
import json, os
from datetime import datetime, timezone

# Configuración de directorio de datos
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DATA_DIR = os.path.abspath(DATA_DIR)

# Ruta del archivo de puntajes
PATH = os.path.join(DATA_DIR, "puntajes.json")


def _ensure_file():
    """
    Crea el archivo de puntajes si no existe.
    
    Crea la estructura de directorios y archivo con formato inicial.
    """
    os.makedirs(DATA_DIR, exist_ok=True)  # Crear directorio si no existe
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            # Formato nuevo: objeto con lista interna para mejor extensibilidad
            json.dump({"scores": []}, f, ensure_ascii=False, indent=2)


def _read():
    """
    Lee el archivo JSON con compatibilidad para formatos antiguos.
    
    Returns:
        Diccionario con lista de scores en formato estandarizado
    """
    _ensure_file()  # Asegurar que el archivo existe
    try:
        with open(PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        # En caso de error, retornar estructura vacía
        return {"scores": []}

    # Compatibilidad con formato viejo (lista plana)
    if isinstance(data, list):
        return {"scores": data}

    # Compatibilidad con formato nuevo (objeto con clave 'scores')
    if isinstance(data, dict) and isinstance(data.get("scores"), list):
        return data

    # Estructura desconocida, retornar vacío
    return {"scores": []}


def load_scores(limit: int | None = None):
    """
    Carga y ordena los puntajes guardados.
    
    Args:
        limit: Cantidad máxima de puntajes a retornar (opcional)
        
    Returns:
        Lista de puntajes ordenados descendente por score
    """
    data = _read()
    scores = data["scores"]
    
    # Ordenar por score descendente, luego por timestamp
    scores_sorted = sorted(
        scores,
        key=lambda s: (s.get("score", 0), s.get("timestamp", "")),
        reverse=True
    )
    
    # Aplicar límite si se especificó
    return scores_sorted[:limit] if limit else scores_sorted


def save_score(entry: dict):
    """
    Guarda un nuevo puntaje en el archivo.
    
    Args:
        entry: Diccionario con datos del puntaje
        
    Returns:
        Entrada normalizada que se guardó
    """
    if not isinstance(entry, dict):
        raise TypeError("entry debe ser un dict")

    # Normalización de campos para consistencia
    normalized = {
        "score": float(entry.get("score", 0.0)),          # Puntaje final
        "income": float(entry.get("income", 0.0)),        # Ingresos base
        "time": float(entry.get("time", 0.0)),            # Tiempo de partida
        "reputation": int(entry.get("reputation", 0)),    # Reputación final
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),  # Marca temporal
    }

    # Leer datos existentes y agregar nuevo puntaje
    data = _read()
    data["scores"].append(normalized)

    # Guardar archivo actualizado
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return normalized