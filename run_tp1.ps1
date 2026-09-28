# Rejoue l'integralite du TP 1 en une seule commande.
#
# A lancer depuis le dossier tp-mlops, PowerShell et le venv actifs
# (.venv\Scripts\Activate.ps1), le serveur MLflow deja demarre dans un autre
# terminal :
#   mlflow server --host 127.0.0.1 --port 5000 `
#                --backend-store-uri sqlite:///mlflow.db `
#                --default-artifact-root ./mlartifacts
#
# Note : dans une chaine entre apostrophes simples, un apostrophe se double
# (''). Les messages restent en ASCII pour s'afficher correctement sous
# Windows PowerShell 5.1, qui lit les .ps1 en ANSI sauf BOM UTF-8.
#
# PYTHONIOENCODING : MLflow 3 imprime un emoji en fin d'execution. La console
# Windows est en cp1252 et ne sait pas l'encoder -> UnicodeEncodeError, qui
# laisse l'execution bloquee au statut RUNNING. On force l'UTF-8.

$env:PYTHONIOENCODING = 'utf-8'
$ErrorActionPreference = 'Stop'

# 1. Donnees
Write-Host '1/2 - generation des donnees...'
python data\data.py

# 2. Serie d'entrainements
Write-Host '2/2 - serie d''entrainements...'
foreach ($p in '100 4', '200 8', '300 12', '500 16', '600 24') {
    $a = $p -split ' '   # decoupe '200 8' en deux arguments
    python src\train.py $a[0] $a[1]
}

Write-Host ''
Write-Host 'TP1 termine - consultez http://127.0.0.1:5000'
