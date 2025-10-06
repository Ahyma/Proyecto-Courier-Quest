import pickle, os

# Configuración de directorio de guardado
SAVE_DIR = os.path.join(os.path.dirname(__file__), "..", "saves")
SAVE_DIR = os.path.abspath(SAVE_DIR)
os.makedirs(SAVE_DIR, exist_ok=True)  # Crear directorio si no existe

def save_slot(filename, state_obj):
    """
    Guarda el estado del juego en un archivo.
    
    Args:
        filename: Nombre del archivo de guardado
        state_obj: Objeto con el estado del juego a guardar
    """
    path = os.path.join(SAVE_DIR, filename)
    with open(path, "wb") as f:
        pickle.dump(state_obj, f, protocol=pickle.HIGHEST_PROTOCOL)

def load_slot(filename):
    """
    Carga el estado del juego desde un archivo.
    
    Args:
        filename: Nombre del archivo de guardado
        
    Returns:
        Estado del juego cargado
    """
    path = os.path.join(SAVE_DIR, filename)
    with open(path, "rb") as f:
        return pickle.load(f)