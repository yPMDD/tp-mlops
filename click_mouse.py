"""Utilitaire d'automatisation souris (hors livrables TP) : clic gauche avec un deplacement instantane."""
import ctypes, sys

user32 = ctypes.windll.user32

def click(x, y):
    user32.SetCursorPos(int(x), int(y))
    user32.mouse_event(2, 0, 0, 0, 0)  # LEFTDOWN
    user32.mouse_event(4, 0, 0, 0, 0)  # LEFTUP

if __name__ == '__main__':
    click(int(sys.argv[1]), int(sys.argv[2]))
    print('clic en', sys.argv[1], sys.argv[2])
