# Clic neutre sur une zone vide de la page (focus page) puis PageDown Forward/Back
# Usage : powershell -File pagedown_capture.ps1 -X 1000 -Y 430 -NPg 1 -Capture captures\...\x.png [-Back]
param(
    [Parameter(Mandatory=$true)][int]$X,
    [Parameter(Mandatory=$true)][int]$Y,
    [Parameter(Mandatory=$true)][int]$NPg,
    [Parameter(Mandatory=$true)][string]$Capture,
    [switch]$Back
)
$ErrorActionPreference = 'Stop'

python window_utils.py 2>$null | Out-Null
Start-Sleep -Milliseconds 400

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class FG4 {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
"@

$brave = Get-Process brave | Where-Object { $_.MainWindowTitle } | Select-Object -First 1
if (-not $brave) { Write-Error 'aucune fenetre Brave'; exit 3 }
$fg = [FG4]::GetForegroundWindow()
if ($fg -ne $brave.MainWindowHandle) { Write-Error "foreground pas brave"; exit 4 }
if ($brave.MainWindowTitle -notmatch 'H2O Flow') { Write-Error "onglet actif: $($brave.MainWindowTitle)"; exit 5 }

python click_mouse.py $X $Y | Out-Null
Start-Sleep -Milliseconds 600
$fg2 = [FG4]::GetForegroundWindow()
if ($fg2 -ne $brave.MainWindowHandle) { Write-Error 'foreground perdu apres clic'; exit 6 }

$ws = New-Object -ComObject WScript.Shell
for ($i=0; $i -lt $NPg; $i++) {
    if ($Back) { $ws.SendKeys('{PGUP}') } else { $ws.SendKeys('{PGDN}') }
    Start-Sleep -Milliseconds 500
}
Start-Sleep -Seconds 2

python -c "from PIL import ImageGrab; ImageGrab.grab().save(r'$Capture')"
Write-Host "clic neutre ($X,$Y) + $($NPg)x PgDn + capture"
