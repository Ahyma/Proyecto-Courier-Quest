# main.py
"""
imports:
pygame: es para gráficos y manejo de eventos
sys: es para funciones del sistema, como salir del programa
os: es para manejo de rutas de archivos
random: es para generar números aleatorios
"""
import pygame
import sys
from game.ai_courier import AIDifficulty
from game.menu import Menu
from game.game_loop import start_game


# ==================== MAIN: MENÚ + PARTIDA ====================

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Courier Quest")

    menu = Menu(screen)
    ai_difficulty = AIDifficulty.MEDIUM

    running = True
    while running:
        action, ai_difficulty = menu.show(ai_difficulty)

        if action == "exit" or action is None:
            running = False

        elif action == "show_scores":
            scores = load_scores()
            print("=== PUNTUACIONES ===")
            for idx, s in enumerate(scores, start=1):
                print(f"{idx}. Score={s['score']} Income={s['income']} Time={s['time']} Rep={s['reputation']}")
            input("Presiona ENTER para volver al menú...")

        elif action == "new_game":
            # Reiniciamos display para que start_game configure la ventana grande
            pygame.display.quit()
            pygame.display.init()
            start_game(ai_difficulty, load_saved=False)
            # Al terminar la partida, volvemos a crear la ventanita del menú
            screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption("Courier Quest")
            menu = Menu(screen)

        elif action == "load_game":
            pygame.display.quit()
            pygame.display.init()
            start_game(ai_difficulty, load_saved=True)
            screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption("Courier Quest")
            menu = Menu(screen)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
