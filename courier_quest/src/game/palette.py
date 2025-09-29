# courier_quest/src/game/palette.py

# Colores de respaldo si faltan imágenes
BLACK = (0, 0, 0)

# Marrón/naranja “tierra” para el patio (fallback genérico)
GROUND = (180, 95, 30)

TILE_COLORS = {
    "C": (100, 100, 100),  # Calles (gris) – sólo se ve si falta sprite
    "P": (50, 200, 50),    # Parques (verde) – sólo se ve si falta sprite
    "B": (50, 50, 50),     # Edificios (gris oscuro) – respaldo si falta PNG

    # Fallbacks muy útiles si el mapa trae otros códigos:
    "T": GROUND,   # tierra
    "G": GROUND,   # ground
    ".": GROUND,   # celdas “vacías” de suelo
    "N": (235, 245, 255),  # nubes si no hay sprite
}
