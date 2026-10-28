"""Deplacement a la molette sur la page sous le curseur (outillage execution).
Usage : python scroll_mouse.py X Y delta  (delta negatif = vers le bas, ex: -360 pour 3 crans)."""
import ctypes, sys

user32 = ctypes.windll.user32
x, y, delta = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
user32.SetCursorPos(x, y)
ctypes.windll.kernel32.Sleep(80)
user32.mouse_event(0x0800, 0, 0, delta, 0)  # MOUSEEVENTF_WHEEL
print('scroll', delta, 'en', x, y)
