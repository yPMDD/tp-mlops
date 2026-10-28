"""Driver d'execution d'une commande dans une cellule H2O Flow (outillage d'execution hors livrables).
Usage : python driver_flow_exec.py "commande Flow" capture.png
- force Brave au premier plan
- bascule (Ctrl+Tab) jusqu'a l'onglet 'H2O Flow'
- selectionne tout le texte de la cellule active, tape la commande, Ctrl+Enter
- screenshot dans le fichier capture donne"""
import sys, time
import window_utils

CMD = sys.argv[1]
CAPTURE = sys.argv[2]

hwnd = window_utils.find_brave_window()
window_utils.force_foreground(hwnd)
time.sleep(0.6)

import ctypes
from ctypes import wintypes
user32 = ctypes.windll.user32
buf = ctypes.create_unicode_buffer(512)
user32.GetWindowTextW(user32.GetForegroundWindow(), buf, 512)
assert user32.GetForegroundWindow() == hwnd, 'foreground=' + buf.value + ', attendu brave'

best = 8
for i in range(10):
    titre = window_utils.window_title(hwnd)
    if 'H2O Flow' in titre:
        break
    if i >= best:  # au dela, passer par Ctrl+Shift+Tab au cas ou on fait le tour complet
        window_utils.press_ctrl(window_utils.VK_TAB)
    window_utils.press_ctrl(window_utils.VK_TAB)
    time.sleep(1.2)

titre = window_utils.window_title(hwnd)
assert 'H2O Flow' in titre, 'onglet H2O Flow non atteint, titre=' + titre
print('onglet OK:', titre)

window_utils.press_ctrl(window_utils.VK_A)          # selection du contenu de la cellule
time.sleep(0.35)
window_utils.type_text(CMD)
time.sleep(0.5)
window_utils.press_ctrl(window_utils.VK_RETURN)     # executer la cellule
time.sleep(3.5)

from PIL import ImageGrab
ImageGrab.grab().save(CAPTURE)
print('commande envoyee, capture:', CAPTURE)
