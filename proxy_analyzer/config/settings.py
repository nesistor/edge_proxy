import os

# Konfiguracja Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Domyślne ustawienia TTL
DEFAULT_TTL = 72 * 3600  # 72 godziny w sekundach
