FROM python:3.11-slim

# Ustawiamy katalog roboczy
WORKDIR /app

# Kopiujemy listę bibliotek
COPY requirements.txt .

# Instalujemy biblioteki
RUN pip install --no-cache-dir -r requirements.txt

# 🔥 WeasyPrint dependencies
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    libxml2 \
    libxslt1.1 \
    libpangocairo-1.0-0 \
    shared-mime-info

# 🔥 Install WeasyPrint
RUN pip install weasyprint
# Kopiujemy resztę plików projektu
COPY . .

# Port dla Django
EXPOSE 8000

# Start serwera
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]