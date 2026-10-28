"""Driver de frappe dans la cellule active de H2O Flow (outillage execution).
Usage : python driver_type.py "cell_command" capture.png
Preconditions : Brave au premier plan + onglet H2O Flow + curseur deja present dans la cellule.
Sequence : Ctrl+A (selection du texte de la cellule) -> saisie -> Ctrl+Enter -> screenshot."""
import sys, time
import window_utils

CMD = sys.argv[1]
CAPTURE = sys.argv[2]

window_utils.press_ctrl(window_utils.VK_A)          # selection de tout le texte de la cellule
time.sleep(0.35)
window_utils.type_text(CMD)
time.sleep(0.6)
window_utils.press_ctrl(window_utils.VK_RETURN)
time.sleep(4.0)

from PIL import ImageGrab
ImageGrab.grab().save(CAPTURE)
print('frappe + ctrl+enter envoyee ; capture:', CAPTURE)
