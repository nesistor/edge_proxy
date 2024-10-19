import redis
import time
from config.settings import REDIS_HOST, REDIS_PORT

class RedisManager:
    def __init__(self):
        self.client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    def get_keys(self, pattern):
        return self.client.keys(pattern)

    def get_request_data(self, key):
        return self.client.hgetall(key)

    def get_last_used_time(self, key):
        # Zakładamy, że dane są przechowywane jako znacznik czasu
        last_used = self.client.hget(key, 'last_used')
        return float(last_used) if last_used else None

    def set_ttl(self, key, ttl):
        self.client.expire(key, ttl)
        print(f"TTL for {key} set to {ttl} seconds.")

    def update_last_used_time(self, key):
        self.client.hset(key, 'last_used', time.time())
