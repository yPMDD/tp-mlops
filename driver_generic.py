"""Driver foreground+onglet (outillage execution). Usage : python driver_generic.py [--light]
Force Brave devant et bascule jusqu'a l'onglet H2O Flow ; trois verifications par titre."""
import sys, time
import window_utils

hwnd = window_utils.find_brave_window()
ok = window_utils.force_foreground(hwnd)
time.sleep(0.6)

import ctypes
user32 = ctypes.windll.user32
buf = ctypes.create_unicode_buffer(512)
user32.GetWindowTextW(user32.GetForegroundWindow(), buf, 512)
print('SetForegroundWindow retour:', ok, '| foreground:', buf.value)

# bascule jusqu a l onglet H2O Flow
for i in range(12):
    titre = window_utils.window_title(hwnd)
    if 'H2O Flow' in titre:
        break
    window_utils.press_ctrl(window_utils.VK_TAB)   # Ctrl+Tab = onglet suivant
    time.sleep(1.0)

titre = window_utils.window_title(hwnd)
print('titre final:', titre)
assert 'H2O Flow' in titre
