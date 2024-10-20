from redis_client import RedisClient
from llama_model import LlamaModel
import time

class RequestAnalyzer:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis = RedisClient(host=redis_host, port=redis_port, db=redis_db)
        self.llama = LlamaModel()

    def analyze_requests(self):
        keys = self.redis.get_all_keys()
        current_time = time.time()

        for key in keys:
            request_data = self.redis.get_request_data(key)
            
            # Analiza zapytania przy pomocy LLaMA
            analysis_result = self.llama.analyze_request(request_data)

            # Sprawdź ile razy request został użyty
            request_count = self.redis.get_request_count(key)

            # Jeżeli request był użyty tylko raz w ciągu 72h, ustaw TTL
            last_used_time = float(request_data.get('last_used', 0))
            if request_count == 1 and (current_time - last_used_time) > 72 * 3600:
                print(f"Setting TTL for {key}")
                self.redis.set_ttl(key, 3600)  # Ustaw TTL na 1 godzinę

            # Zwiększenie liczby użyć requesta
            self.redis.increment_request_count(key)

    def run(self):
        # Uruchom analizę zapytań cyklicznie
        while True:
            self.analyze_requests()
            time.sleep(600)  # Co 10 minut
