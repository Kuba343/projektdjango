# Używamy oficjalnego obrazu Pythona
FROM python:3.11-slim

# Ustawiamy katalog roboczy
WORKDIR /app

# Instalujemy zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiujemy resztę projektu
COPY . .

# Otwieramy port dla Django
EXPOSE 8000

# Komenda startowa
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]