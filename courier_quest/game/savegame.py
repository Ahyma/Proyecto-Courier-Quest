# src/savegame.py
import pickle, os

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
