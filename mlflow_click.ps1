# Clic + capture pour le registre MLflow (titre non contraint).
# Usage : powershell -File mlflow_click.ps1 -X 250 -Y 420 -Capture captures\tp6\x.png
param(
    [Parameter(Mandatory=$true)][int]$X,
    [Parameter(Mandatory=$true)][int]$Y,
    [Parameter(Mandatory=$true)][string]$Capture
)
$ErrorActionPreference = 'Stop'

python window_utils.py 2>$null | Out-Null
Start-Sleep -Milliseconds 400

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class FG6 {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
"@

$brave = Get-Process brave | Where-Object { $_.MainWindowTitle } | Select-Object -First 1
if (-not $brave) { Write-Error 'aucune fenetre Brave'; exit 3 }
$fg = [FG6]::GetForegroundWindow()
if ($fg -ne $brave.MainWindowHandle) { Write-Error "foreground pas brave ($($brave.MainWindowTitle))"; exit 4 }

python click_mouse.py $X $Y | Out-Null
Start-Sleep -Seconds 3

$fg2 = [FG6]::GetForegroundWindow()
if ($fg2 -ne $brave.MainWindowHandle) { Write-Error 'foreground perdu apres clic'; exit 6 }

python -c "from PIL import ImageGrab; ImageGrab.grab().save(r'$Capture')"
Write-Host "clic ($X,$Y) + capture : $Capture"
