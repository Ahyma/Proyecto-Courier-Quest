# src/scoreboard.py
import json, os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DATA_DIR = os.path.abspath(DATA_DIR)
PATH = os.path.join(DATA_DIR, "puntajes.json")

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
