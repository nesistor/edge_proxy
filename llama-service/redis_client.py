import redis
import json

# Klient Redis
class RedisClient:
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)

    def get_request_data(self, key):
        # Pobierz dane dla danego klucza
        data = self.client.hgetall(key)
        return data

    def set_ttl(self, key, ttl_seconds):
        # Ustaw TTL dla klucza
        self.client.expire(key, ttl_seconds)

    def get_all_keys(self, pattern='proxy:*'):
        # Pobierz wszystkie klucze pasujące do wzorca
        return self.client.keys(pattern)

    def get_request_count(self, key):
        # Pobierz liczbę żądań zliczając wystąpienia
        return int(self.client.hget(key, "request_count") or 0)

    def increment_request_count(self, key):
        # Zwiększ licznik zapytań
        self.client.hincrby(key, "request_count", 1)
