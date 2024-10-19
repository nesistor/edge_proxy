from redis_manager import RedisManager
from llama_integration import LlamaModel
import time

class ProxyRequestAnalyzer:
    def __init__(self, redis_manager, llama_model):
        self.redis_manager = redis_manager
        self.llama_model = llama_model

    def analyze_and_set_ttl(self):
        # Pobierz wszystkie klucze proxy
        keys = self.redis_manager.get_keys("proxy:*")
        current_time = time.time()

        for key in keys:
            # Pobierz szczegóły hasza z Redis
            request_data = self.redis_manager.get_request_data(key)
            purpose = request_data.get("purpose", "empty")

            # Jeśli zapytanie ma cel 'refresh', nie ustawiamy TTL
            if purpose == "refresh":
                continue

            # Sprawdź, kiedy ostatnio zapytanie było użyte
            last_used = self.redis_manager.get_last_used_time(key)

            # Sprawdź, czy zapytanie było użyte tylko raz w ciągu ostatnich 72 godzin
            if last_used and (current_time - last_used > 72 * 3600):
                # Użyj modelu LLaMA do określenia TTL na podstawie wzorców
                ttl = self.llama_model.determine_ttl(request_data)
                self.redis_manager.set_ttl(key, ttl)

if __name__ == "__main__":
    redis_manager = RedisManager()
    llama_model = LlamaModel()
    analyzer = ProxyRequestAnalyzer(redis_manager, llama_model)
    analyzer.analyze_and_set_ttl()
