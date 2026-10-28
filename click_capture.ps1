# Clic souris avec garde-fou foreground + capture (outillage execution, hors livrables).
# Usage : powershell -File click_capture.ps1 -X 190 -Y 532 -Capture captures\...\x.png -WaitSec 3
param(
    [Parameter(Mandatory=$true)][int]$X,
    [Parameter(Mandatory=$true)][int]$Y,
    [Parameter(Mandatory=$true)][string]$Capture,
    [int]$WaitSec = 3
)
$ErrorActionPreference = 'Stop'

python window_utils.py 2>$null | Out-Null
Start-Sleep -Milliseconds 400

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class FG2 {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
"@

$brave = Get-Process brave | Where-Object { $_.MainWindowTitle } | Select-Object -First 1
if (-not $brave) { Write-Error 'aucune fenetre Brave'; exit 3 }
$fg = [FG2]::GetForegroundWindow()
if ($fg -ne $brave.MainWindowHandle) { Write-Error "foreground pas brave"; exit 4 }
if ($brave.MainWindowTitle -notmatch 'H2O Flow') { Write-Error "onglet actif: $($brave.MainWindowTitle)"; exit 5 }

python click_mouse.py $X $Y | Out-Null
Start-Sleep -Milliseconds ($WaitSec * 1000)

$fg2 = [FG2]::GetForegroundWindow()
if ($fg2 -ne $brave.MainWindowHandle) { Write-Error 'foreground perdu apres clic'; exit 6 }

python -c "from PIL import ImageGrab; ImageGrab.grab().save(r'$Capture')"
Write-Host "clic ($X,$Y) + capture : $Capture"
