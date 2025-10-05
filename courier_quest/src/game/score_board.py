# courier_quest/src/game/score_board.py
import json, os
from datetime import datetime, timezone

# Carpeta data/ junto al paquete src/
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DATA_DIR = os.path.abspath(DATA_DIR)

# Mantengo el mismo nombre de archivo que usabas
PATH = os.path.join(DATA_DIR, "puntajes.json")


def _ensure_file():
    """Crea la carpeta y el archivo si no existen."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            # Formato nuevo: objeto con lista interna
            json.dump({"scores": []}, f, ensure_ascii=False, indent=2)


def _read():
    """Lee el JSON tolerando el formato viejo (lista) y el nuevo ({'scores': [...]})"""
    _ensure_file()
    try:
        with open(PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"scores": []}

    # Compatibilidad con formato viejo (lista plana)
    if isinstance(data, list):
        return {"scores": data}

    if isinstance(data, dict) and isinstance(data.get("scores"), list):
        return data

    return {"scores": []}


def load_scores(limit: int | None = None):
    """
    Devuelve la lista de puntajes ordenada desc por 'score' (y luego por fecha).
    limit: opcional, cantidad máxima a retornar.
    """
    data = _read()
    scores = data["scores"]
    scores_sorted = sorted(
        scores,
        key=lambda s: (s.get("score", 0), s.get("timestamp", "")),
        reverse=True
    )
    return scores_sorted[:limit] if limit else scores_sorted


def save_score(entry: dict):
    """
    Guarda un puntaje. 'entry' puede traer:
      - score (float)
      - income (float)
      - time (float)  -> segundos de partida
      - reputation (int)
    Se agrega automáticamente 'timestamp' en UTC.
    """
    if not isinstance(entry, dict):
        raise TypeError("entry debe ser un dict")

    # Normalización de campos
    normalized = {
        "score": float(entry.get("score", 0.0)),
        "income": float(entry.get("income", 0.0)),
        "time": float(entry.get("time", 0.0)),
        "reputation": int(entry.get("reputation", 0)),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    data = _read()
    data["scores"].append(normalized)

    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return normalized
