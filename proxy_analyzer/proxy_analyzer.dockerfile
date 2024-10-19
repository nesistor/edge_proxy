FROM python:3.9-slim

WORKDIR /app

# Instalacja zależności
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Kopiowanie plików aplikacji
COPY . .

# Komenda startowa
CMD ["python", "scripts/analyze_requests.py"]
