#!/usr/bin/env bash
set -e                                     # arret au premier echec
python donnees.py                          # 1. donnees

for p in '100 4' '200 8' '300 12' '500 16' '600 24'; do
  python src/train.py $p                   # 2. serie d'entrainements
done
echo 'TP1 termine - consultez http://127.0.0.1:5000'