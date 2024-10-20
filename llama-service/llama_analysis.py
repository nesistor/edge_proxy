import torch
from transformers import pipeline
import time
from redis_client import RedisClient

# Class to handle the LLaMA model
class LlamaModel:
    def __init__(self, model_id='meta-llama/Llama-3.2-1B-Instruct'):
        self.pipe = pipeline(
            'text-generation',
            model=model_id,
            torch_dtype=torch.bfloat16,
            device_map='auto'
        )

    def analyze_request(self, request_data):
    # Enhanced conversation for intelligent analysis
    conversation = [
        {
            "role": "system",
            "content": (
                "You are a request analysis assistant. "
                "Based on the provided request data, analyze the following parameters: "
                "- request_method (GET, POST, etc.) "
                "- request_url (the URL being requested) "
                "- request_headers (relevant headers, such as User-Agent) "
                "- response (the expected or previous response) "
                "- purpose (current purpose of the request) "
                "- request_count (the number of times this request has been made) "
                "If the request is repeated (request_count > 1), it should be considered for deletion. "
                "If a POST request has been made to the same URL previously, it should be marked for refreshing. "
                "Additionally, assess the response data to determine if it contains dynamically changing information. "
                "If the response contains dynamic data, automatically set the purpose to 'dynamic'. "
                "Return one of the following options: 'delete' to remove the request, "
                "'refresh' to mark it for refreshing, or 'keep' to keep it as is."
            )
        },
        {
            "role": "user",
            "content": (
                f"Analyze the following request data:\n"
                f"Request Method: {request_data['request_method']}\n"
                f"Request URL: {request_data['request_url']}\n"
                f"Request Headers: {request_data['request_headers']}\n"
                f"Response: {request_data['response']}\n"
                f"Current Purpose: {request_data.get('purpose', 'unknown')}\n"
                f"Request Count: {request_data.get('request_count', 0)}\n"
                "Please provide a recommendation based on this analysis."
            )
        }
    ]

    try:
        output = self.pipe(conversation, max_new_tokens=150)
        analysis_result = output[0]['generated_text'].strip().lower()  # Clean the output for comparison
    except Exception as e:
        print(f"Error during model inference: {e}")
        return 'keep'  # Default action on error
    
    # Check if LLaMA suggests the data is dynamic
    if 'dynamic' in analysis_result:
        request_data['purpose'] = 'dynamic'
        
    # Return a decision based on LLaMA's response
    if 'delete' in analysis_result:
        return 'delete'
    elif 'refresh' in analysis_result:
        return 'refresh'
    else:
        return 'keep'

    
    def compare_urls(self, url1, url2):
        # LLaMA analyzes the similarity of URLs
        conversation = [
            {"role": "system", "content": "You are an assistant that analyzes URL similarity."},
            {"role": "user", "content": f"Are the following URLs similar? URL1: {url1}, URL2: {url2}. Return 'True' if similar, otherwise 'False'."}
        ]
        try:
            output = self.pipe(conversation, max_new_tokens=50)
            result = output[0]['generated_text'].strip().lower()
        except Exception as e:
            print(f"Error during URL comparison: {e}")
            return False  # Default to not similar on error

        # We assume the model returns 'True' or 'False'
        return 'true' in result

# Class to analyze requests stored in Redis
class RequestAnalyzer:
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis = RedisClient(host=redis_host, port=redis_port, db=redis_db)
        self.llama = LlamaModel()

    def analyze_requests(self):
        keys = self.redis.get_all_keys()
        current_time = time.time()

        for key in keys:
            try:
                request_data = self.redis.get_request_data(key)
                # Analyze the request using LLaMA
                action = self.llama.analyze_request(request_data)

                if action == 'delete':
                    print(f"Request {key} flagged for deletion.")
                    self.redis.delete_request(key)
                elif action == 'refresh':
                    print(f"Request {key} marked for refreshing.")
                    self.redis.client.hset(key, "purpose", "refresh")
                else:
                    print(f"Request {key} will be kept with no changes.")
                    self.redis.client.hset(key, "purpose", "keep")

                # Check if the request was used only once in the last 72 hours and set TTL
                request_count = self.redis.get_request_count(key)
                last_used_time = float(request_data.get('last_used', 0))
                if request_count == 1 and (current_time - last_used_time) > 72 * 3600:
                    print(f"Setting TTL for {key}")
                    self.redis.set_ttl(key, 3600)  # Set TTL to 1 hour

                # Check if it's a POST request and if it has a similar API/URL
                if request_data["request_method"] == "POST":
                    print(f"POST request detected: {key}. Deleting old related requests and marking related GET requests as 'refresh'.")
                    self.delete_old_requests(request_data["request_url"])
                    self.delete_old_duplicate_requests(request_data["request_url"])

                    # Mark GET requests with a similar URL as "refresh"
                    self.mark_related_get_as_refresh(request_data["request_url"])

                # Increment the usage count of the request
                self.redis.increment_request_count(key)

            except Exception as e:
                print(f"Error analyzing request {key}: {e}")

    def delete_old_duplicate_requests(self, request_url):
        all_keys = self.redis.get_all_keys()
        newest_time = None
        newest_key = None

        # Find the newest request with the same URL
        for key in all_keys:
            request_data = self.redis.get_request_data(key)
            if request_data["request_url"] == request_url:
                request_time = float(request_data.get('last_used', 0))
                if newest_time is None or request_time > newest_time:
                    newest_time = request_time
                    newest_key = key

        # Delete all older requests with the same URL
        if newest_key:
            for key in all_keys:
                request_data = self.redis.get_request_data(key)
                if request_data["request_url"] == request_url:
                    request_time = float(request_data.get('last_used', 0))
                    if request_time < newest_time:
                        print(f"Deleting older request {key} for URL {request_data['request_url']}")
                        self.redis.delete_request(key)

    def mark_related_get_as_refresh(self, request_url):
        all_keys = self.redis.get_all_keys()
        for key in all_keys:
            request_data = self.redis.get_request_data(key)
            # LLaMA decides if the GET request is similar to the POST
            if request_data["request_method"] == "GET" and self.llama.compare_urls(request_data["request_url"], request_url):
                print(f"Marking GET request {key} as 'refresh' for URL {request_data['request_url']}")
                self.redis.client.hset(key, "purpose", "refresh")

    def run(self):
        while True:
            self.analyze_requests()
            time.sleep(600)  # Every 10 minutes
