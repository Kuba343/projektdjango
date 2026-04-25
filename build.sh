#!/usr/bin/env bash
# Wyjście przy błędzie
set -o errexit

# Instalacja bibliotek
pip install -r requirements.txt

# Zbieranie plików statycznych
python manage.py collectstatic --no-input

# Migracja bazy danych (Neon)
python manage.py migrate