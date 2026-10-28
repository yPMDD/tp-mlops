# Deplacement molette avec garde-fou foreground + capture (outillage execution).
# Usage : powershell -File scroll_capture.ps1 -X 800 -Y 600 -Delta -720 -Capture captures\...\x.png
param(
    [Parameter(Mandatory=$true)][int]$X,
    [Parameter(Mandatory=$true)][int]$Y,
    [Parameter(Mandatory=$true)][int]$Delta,
    [Parameter(Mandatory=$true)][string]$Capture,
    [int]$WaitSec = 2
)
$ErrorActionPreference = 'Stop'

python window_utils.py 2>$null | Out-Null
Start-Sleep -Milliseconds 400

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class FG3 {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
"@

$brave = Get-Process brave | Where-Object { $_.MainWindowTitle } | Select-Object -First 1
if (-not $brave) { Write-Error 'aucune fenetre Brave'; exit 3 }
$fg = [FG3]::GetForegroundWindow()
if ($fg -ne $brave.MainWindowHandle) { Write-Error "foreground pas brave"; exit 4 }
if ($brave.MainWindowTitle -notmatch 'H2O Flow') { Write-Error "onglet actif: $($brave.MainWindowTitle)"; exit 5 }

python scroll_mouse.py $X $Y $Delta | Out-Null
Start-Sleep -Milliseconds ($WaitSec * 1000)

python -c "from PIL import ImageGrab; ImageGrab.grab().save(r'$Capture')"
Write-Host "scroll $Delta + capture : $Capture"
