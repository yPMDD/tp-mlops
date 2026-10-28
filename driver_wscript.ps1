# Driver de frappe DANS la cellule H2O Flow via WScript.SendKeys (outillage execution, hors livrables).
# Garde-fou : verifie que la fenetre de premier plan est bien Brave + onglet H2O Flow avant d'envoyer la moindre touche.
# Usage : powershell -File driver_wscript.ps1 -Text "getLeaderboard ..." -Capture captures\...\x.png
param(
    [Parameter(Mandatory=$true)][string]$Command,
    [Parameter(Mandatory=$true)][string]$Arg,
    [Parameter(Mandatory=$true)][string]$Capture,
    [int]$ClickX = 880,
    [int]$ClickY = 267
)
$ErrorActionPreference = 'Stop'
# reconstitution de la commande avec guillemets doubles SANS passer par la ligne de commande
$Text = $Command + ' "' + $Arg + '"'

# 1) forcer Brave au premier plan (helper python eprouve)
python window_utils.py 2>$null | Out-Null
Start-Sleep -Milliseconds 400

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class FG {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
"@

# 2) garde-fou : foreground == fenetre principale Brave ET titre contient H2O Flow
$brave = Get-Process brave | Where-Object { $_.MainWindowTitle } | Select-Object -First 1
if (-not $brave) { Write-Error 'aucune fenetre Brave'; exit 3 }
$fg = [FG]::GetForegroundWindow()
if ($fg -ne $brave.MainWindowHandle) { Write-Error "foreground=$(fg) pas brave ($($brave.MainWindowHandle))"; exit 4 }
if ($brave.MainWindowTitle -notmatch 'H2O Flow') { Write-Error "onglet actif: $($brave.MainWindowTitle)"; exit 5 }
Write-Host "garde-fou OK : $($brave.MainWindowTitle)"

$ws = New-Object -ComObject WScript.Shell

# 3) fermer une eventuelle barre de recherche ouverte, puis clic prealable dans la cellule
$ws.SendKeys('{ESC}')
Start-Sleep -Milliseconds 350
python click_mouse.py $ClickX $ClickY | Out-Null
Start-Sleep -Milliseconds 700
$fg2 = [FG]::GetForegroundWindow()
if ($fg2 -ne $brave.MainWindowHandle) { Write-Error 'foreground perdu apres clic'; exit 6 }

# 4) selection du texte de la cellule -> frappe -> execution
$ws.SendKeys('^a')
Start-Sleep -Milliseconds 400
$ws.SendKeys($Text)
Start-Sleep -Milliseconds 500
$ws.SendKeys('^{ENTER}')
Start-Sleep -Seconds 5

# 5) capture
python -c "from PIL import ImageGrab; ImageGrab.grab().save(r'$Capture')"
Write-Host "frappe envoyee via SendKeys ; capture : $Capture"
