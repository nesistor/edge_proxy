import torch
from transformers import pipeline
import time
from redis_client import RedisClient

# Klasa do obsługi modelu LLaMA
class LlamaModel:
    def __init__(self, model_id='meta-llama/Llama-3.2-1B-Instruct'):
        self.pipe = pipeline(
            'text-generation',
            model=model_id,
            torch_dtype=torch.bfloat16,
            device_map='auto'
        )

    def analyze_request(self, request_data):
        # Analiza requestu za pomocą LLaMA
        conversation = [
            {"role": "system", "content": "You are a request analysis assistant. Based on the request data, return one of three options: 'delete' to remove the request, 'refresh' to mark it for refreshing, or 'keep' to keep it as is."},
            {"role": "user", "content": f"Analyze the following request: {request_data}"}
        ]
        output = self.pipe(conversation, max_new_tokens=150)
        analysis_result = output[0]['generated_text']
        
        # Zwróć decyzję na podstawie odpowiedzi LLaMA
        if 'delete' in analysis_result.lower():
            return 'delete'
        elif 'refresh' in analysis_result.lower():
            return 'refresh'
        else:
            return 'keep'

    def compare_urls(self, url1, url2):
        # LLaMA analizuje podobieństwo URL-i
        conversation = [
            {"role": "system", "content": "You are an assistant that analyzes URL similarity."},
            {"role": "user", "content": f"Are the following URLs similar? URL1: {url1}, URL2: {url2}. Return 'True' if similar, otherwise 'False'."}
        ]
        output = self.pipe(conversation, max_new_tokens=50)
        result = output[0]['generated_text']
        
        # Zakładamy, że model zwróci 'True' lub 'False'
        return 'true' in result.lower()

# Klasa do analizy requestów zapisanych w Redis
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
            action = self.llama.analyze_request(request_data)

            if action == 'delete':
                print(f"Request {key} flagged for deletion.")
                self.redis.delete_request(key)
            elif action == 'refresh':
                print(f"Request {key} marked for refreshing.")
                self.redis.client.hset(key, "purpose", "refresh")
            else:
                print(f"Request {key} will be kept with no changes.")
                self.redis.client.hset(key, "purpose", "empty")

            # Sprawdź, czy request był użyty tylko raz w ciągu 72h, ustaw TTL
            request_count = self.redis.get_request_count(key)
            last_used_time = float(request_data.get('last_used', 0))
            if request_count == 1 and (current_time - last_used_time) > 72 * 3600:
                print(f"Setting TTL for {key}")
                self.redis.set_ttl(key, 3600)  # Ustaw TTL na 1 godzinę

            # Sprawdź, czy jest to POST request i czy ma podobny API/URL
            if request_data["request_method"] == "POST":
                print(f"POST request detected: {key}. Deleting old related requests and marking related GET requests as 'refresh'.")
                # Usuń stare requesty
                self.delete_old_requests(request_data["request_url"])
                
                # Oznacz GET-y o podobnym URL jako "refresh"
                self.mark_related_get_as_refresh(request_data["request_url"])

            # Zwiększenie liczby użyć requesta
            self.redis.increment_request_count(key)

    # Funkcja usuwa stare requesty o podobnym URL (teraz porównywane przez LLaMA)
    def delete_old_requests(self, request_url):
        all_keys = self.redis.get_all_keys()
        for key in all_keys:
            request_data = self.redis.get_request_data(key)
            # LLaMA decyduje, czy URL-e są podobne
            if self.llama.compare_urls(request_data["request_url"], request_url):
                print(f"Deleting old request {key} for URL {request_data['request_url']}")
                self.redis.delete_request(key)

    # Oznacz powiązane GET requesty jako "refresh" (porównanie przez LLaMA)
    def mark_related_get_as_refresh(self, request_url):
        all_keys = self.redis.get_all_keys()
        for key in all_keys:
            request_data = self.redis.get_request_data(key)
            # LLaMA decyduje, czy GET request jest podobny do POST
            if request_data["request_method"] == "GET" and self.llama.compare_urls(request_data["request_url"], request_url):
                print(f"Marking GET request {key} as 'refresh' for URL {request_data['request_url']}")
                self.redis.client.hset(key, "purpose", "refresh")

    # Uruchom analizę zapytań cyklicznie
    def run(self):
        while True:
            self.analyze_requests()
            time.sleep(600)  # Co 10 minut
