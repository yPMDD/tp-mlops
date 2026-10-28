"""Utilitaire d'automatisation de fenetres (hors livrables TP : seul l'outillage d'execution).
Outils : forcer Brave au premier plan, verifier le titre d'onglet actif,
selectionner le texte d'une cellule H2O Flow, taper une commande, Ctrl+Enter."""
import ctypes, time, sys
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# ---- Structures SendInput (le union DOIT contenir MOUSEINPUT pour avoir la taille systeme 40 sur x64) ----
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class _INPUT_U(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("ii", _INPUT_U)]

INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL = 0x11
VK_RETURN = 0x0D
VK_A = 0x41
VK_TAB = 0x09

def _key(vk, up=False):
    i = INPUT(type=INPUT_KEYBOARD)
    i.ii.ki = KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP if up else 0, 0, None)
    user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INPUT))

def press_ctrl(vk):
    _key(VK_CONTROL)
    time.sleep(0.03)
    _key(vk)
    time.sleep(0.03)
    _key(vk, up=True)
    _key(VK_CONTROL, up=True)

def type_text(text):
    n = len(text) * 2
    lst = (INPUT * n)()
    idx = 0
    for ch in text:
        lst[idx].ii.ki = KEYBDINPUT(0, ord(ch), KEYEVENTF_UNICODE, 0, None)
        lst[idx+1].ii.ki = KEYBDINPUT(0, ord(ch), KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, None)
        idx += 2
    sent = user32.SendInput(n, lst, ctypes.sizeof(INPUT))
    if sent != n:
        print('AVERTISSEMENT SendInput chars envoyes', sent, '/', n)
    time.sleep(0.002 * max(1, len(text)))

def find_brave_window():
    """hwnd de la fenetre principale visible du navigateur Brave (titre non vide + surface max)."""
    import ctypes
    from ctypes import wintypes
    candidates = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == PID():
                titre = window_title(hwnd)
                r = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(r))
                aire = max(0, r.right - r.left) * max(0, r.bottom - r.top)
                candidates.append((aire, bool(titre), hwnd))
        return True
    user32.EnumWindows(cb, 0)
    if not candidates:
        return None
    candidates.sort(reverse=True)   # surface decroissante, titre non vide en priorite
    return candidates[0][2]

_PID_CACHE = None

def PID():
    """PID du navigateur Brave avec fenetre visible (detecte automatiquement)."""
    global _PID_CACHE
    if _PID_CACHE:
        return _PID_CACHE
    import subprocess
    out = subprocess.run(['powershell', '-NoProfile', '-Command',
                          "(Get-Process brave | Where-Object { $_.MainWindowTitle } | Select-Object -First 1).Id"],
                         capture_output=True, text=True).stdout.strip()
    _PID_CACHE = int(out)
    return _PID_CACHE

def window_title(hwnd):
    buf = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, buf, 512)
    return buf.value

def force_foreground(hwnd):
    # deco classique : simuler ALT pour liberer le foreground-lock de Windows
    _key(0x12)      # VK_MENU ALT down
    _key(0x12, up=True)
    time.sleep(0.05)
    # SW_RESTORE si minimise
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        time.sleep(0.5)
    cur_thread = kernel32.GetCurrentThreadId()
    fg_thread = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
    user32.AttachThreadInput(cur_thread, fg_thread, True)
    user32.AttachThreadInput(fg_thread, cur_thread, True)
    user32.BringWindowToTop(hwnd)
    ok = user32.SetForegroundWindow(hwnd)
    user32.AttachThreadInput(cur_thread, fg_thread, False)
    user32.AttachThreadInput(fg_thread, cur_thread, False)
    return bool(ok)

if __name__ == '__main__':
    hwnd = find_brave_window()
    print('hwnd:', hwnd, '| titre:', window_title(hwnd) if hwnd else None)
    if hwnd:
        force_foreground(hwnd)
        time.sleep(0.8)
        print('titre actif:', window_title(hwnd))
