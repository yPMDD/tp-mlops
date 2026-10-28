# Navigation URL + capture (registre MLflow) -- garde-fou foreground Brave sans contrainte de titre.
# Usage : powershell -File mlflow_capture.ps1 -Url 'http://127.0.0.1:5000/#/models' -Capture captures\tp6\registre_1.png
param(
    [Parameter(Mandatory=$true)][string]$Url,
    [Parameter(Mandatory=$true)][string]$Capture
)
$ErrorActionPreference = 'Stop'

python -c "import webbrowser; webbrowser.open('$Url')" | Out-Null
Start-Sleep -Milliseconds 2500
python window_utils.py 2>$null | Out-Null
Start-Sleep -Milliseconds 400

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class FG5 {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
"@

$brave = Get-Process brave | Where-Object { $_.MainWindowTitle } | Select-Object -First 1
if (-not $brave) { Write-Error 'aucune fenetre Brave'; exit 3 }
$fg = [FG5]::GetForegroundWindow()
if ($fg -ne $brave.MainWindowHandle) { Write-Error "foreground pas brave ($($brave.MainWindowTitle))"; exit 4 }

Start-Sleep -Milliseconds 1500
python -c "from PIL import ImageGrab; ImageGrab.grab().save(r'$Capture')"
Write-Host "navigation $Url ; capture : $Capture"
