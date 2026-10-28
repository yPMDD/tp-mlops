"""Driver ATOMIQUE H2O Flow (outillage execution, un seul process, aucune course au foreground).
Usage : python flow_atomic.py <url_flow_absente=1> "commande" capture.png
Etapes : nouvel onglet Flow actif -> foreground verifie -> clic dans la cellule -> Ctrl+A ->
saisie de la commande -> Ctrl+Enter -> screenshot."""
import sys, time, ctypes, webbrowser
import window_utils

user32 = ctypes.windll.user32

CMD = sys.argv[1]
CAPTURE = sys.argv[2]

# 1) nouvel onglet H2O Flow (deviendra actif dans la fenetre brave)
webbrowser.open('http://127.0.0.1:54321')
time.sleep(6)

# 2) foreground + verification
hwnd = window_utils.find_brave_window()
window_utils.force_foreground(hwnd)
time.sleep(0.9)
buf = ctypes.create_unicode_buffer(512)
user32.GetWindowTextW(user32.GetForegroundWindow(), buf, 512)
assert 'H2O Flow' in buf.value, 'foreground/titre inattendu : ' + buf.value
print('foreground OK :', buf.value)

# 3) clic dans la premiere cellule (curseur code flow, y~267 plein ecran 1920x1080)
import click_mouse
click_mouse.click(880, 267)
time.sleep(1.0)

# 4) Ctrl+A puis saisie puis Ctrl+Enter
window_utils.press_ctrl(window_utils.VK_A)
time.sleep(0.35)
window_utils.type_text(CMD)
time.sleep(0.6)
window_utils.press_ctrl(window_utils.VK_RETURN)
time.sleep(4.5)

# 5) capture
from PIL import ImageGrab
ImageGrab.grab().save(CAPTURE)
print('fin :', CAPTURE)
