"""Ouvre un onglet H2O Flow actif dans Brave et place le curseur dans la premiere cellule (outillage execution).
Sequence : webbrowser.open (nouvel onglet actif) ; verification titre ; clic souris dans la cellule."""
import sys, time, webbrowser
import window_utils, ctypes

user32 = ctypes.windll.user32

webbrowser.open('http://127.0.0.1:54321')
time.sleep(6)

hwnd = window_utils.find_brave_window()
window_utils.force_foreground(hwnd)
time.sleep(0.8)

buf = ctypes.create_unicode_buffer(512)
user32.GetWindowTextW(user32.GetForegroundWindow(), buf, 512)
titre = buf.value
print('titre fenetre active:', titre)

if 'H2O Flow' not in titre:
    # repli : click sur l onglet H2O Flow dans la barre d onglets (coordonnee de l onglet 9-10)
    raise SystemExit('onglet H2O Flow non active automatiquement')

# clic dans la premiere cellule (zone de code, y ~265 sur un affichage 1920x1080 plein ecran)
import click_mouse
click_mouse.click(880, 267)
time.sleep(1.0)

from PIL import ImageGrab
ImageGrab.grab().save('captures/tp6/diag_cellule_focus.png')
print('curseur place dans la cellule')
