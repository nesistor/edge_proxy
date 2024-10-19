# Wybierz obraz Pythona
FROM python:3.9-slim

# Ustawienie katalogu roboczego
WORKDIR /app

# Kopiowanie pliku z zależnościami
COPY requirements.txt ./

# Instalacja zależności
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie kodu źródłowego
COPY . .

# Ustawienie polecenia domyślnego
CMD ["python", "services/llama_service.py"]
