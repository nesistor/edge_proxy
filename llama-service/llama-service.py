import threading
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, DataCollatorForLanguageModeling, pipeline
from datasets import Dataset
from redis_client import RedisClient

class LlamaTrainer:
    def __init__(self, model_id='meta-llama/Llama-3.2-1B-Instruct', redis_host='localhost', redis_port=6379, redis_db=0):
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16,
            device_map='auto'
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.redis = RedisClient(host=redis_host, port=redis_port, db=redis_db)

    def get_training_data(self):
        keys = self.redis.get_all_keys()
        data = []

        for key in keys:
            request_data = self.redis.get_request_data(key)
            if 'request_url' in request_data and 'response' in request_data:
                input_text = f"Request URL: {request_data['request_url']}\nResponse: {request_data['response']}"
                data.append(input_text)

        return data

    def prepare_dataset(self, data):
        dataset = Dataset.from_dict({"text": data})

        def tokenize_function(examples):
            return self.tokenizer(examples["text"], padding="max_length", truncation=True, max_length=512)

        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        return tokenized_dataset

    def fine_tune_model(self, tokenized_dataset):
        training_args = TrainingArguments(
            output_dir="./llama_finetuned",
            overwrite_output_dir=True,
            num_train_epochs=3,
            per_device_train_batch_size=4,
            save_steps=10_000,
            save_total_limit=2,
            fp16=True,
            logging_dir='./logs',
        )

        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer, mlm=False
        )

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
        )

        trainer.train()

    def run_training(self):
        print("Fetching data from Redis...")
        data = self.get_training_data()
        if not data:
            print("No data to train on.")
            return

        print("Preparing dataset...")
        tokenized_dataset = self.prepare_dataset(data)

        print("Starting fine-tuning of LLaMA model...")
        self.fine_tune_model(tokenized_dataset)
        print("Fine-tuning completed.")

    def update_cache(self, request_data):
        self.redis.store_request_data(request_data)

class LlamaModel:
    def __init__(self, model_id='meta-llama/Llama-3.2-1B-Instruct', guard_model_id="meta-llama/Llama-Guard-3-1B"):
        self.pipe = pipeline(
            'text-generation',
            model=model_id,
            torch_dtype=torch.bfloat16,
            device_map='auto'
        )
        self.guard_tokenizer = AutoTokenizer.from_pretrained(guard_model_id)
        self.guard_model = AutoModelForCausalLM.from_pretrained(
            guard_model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )

    def check_inappropriate_content(self, user_input):
        input_text = f"<|user|> {user_input} "
        input_ids = self.guard_tokenizer.encode(input_text, return_tensors='pt').to(self.guard_model.device)

        with torch.no_grad():
            output_ids = self.guard_model.generate(
                input_ids,
                max_length=input_ids.size(1) + 50,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.guard_tokenizer.eos_token_id
            )

        output_text = self.guard_tokenizer.decode(output_ids[0], skip_special_tokens=True)
        response = output_text[len(input_text):].strip()

        if "no" in response.lower() or "not allowed" in response.lower():
            print("Inappropriate request detected.")
            return False

        return True

    def analyze_request(self, request_data):
        conversation = [
            {
                "role": "system",
                "content": (
                    "You are a request analysis assistant. "
                    "Analyze the following request data: method, URL, headers, response, purpose, request count."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Request Method: {request_data['request_method']}\n"
                    f"Request URL: {request_data['request_url']}\n"
                    f"Request Headers: {request_data['request_headers']}\n"
                    f"Response: {request_data['response']}\n"
                    f"Request Count: {request_data.get('request_count', 0)}"
                )
            }
        ]

        try:
            output = self.pipe(conversation, max_new_tokens=150)
            analysis_result = output[0]['generated_text'].strip().lower()
        except Exception as e:
            print(f"Error during model inference: {e}")
            return 'keep'

        if 'delete' in analysis_result:
            return 'delete'
        elif 'refresh' in analysis_result:
            return 'refresh'
        else:
            return 'keep'

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

                if not self.llama.check_inappropriate_content(request_data['request_url']):
                    print(f"Request {key} contains inappropriate content and will be ignored.")
                    continue

                action = self.llama.analyze_request(request_data)

                if action == 'delete':
                    print(f"Request {key} flagged for deletion.")
                    self.redis.delete_request(key)
                elif action == 'refresh':
                    print(f"Request {key} marked for refreshing.")
                    self.redis.client.hset(key, "purpose", "refresh")
                else:
                    print(f"Request {key} will be kept as is.")
                    self.redis.client.hset(key, "purpose", "keep")

                request_count = self.redis.get_request_count(key)
                last_used_time = float(request_data.get('last_used', 0))
                if request_count == 1 and (current_time - last_used_time) > 72 * 3600:
                    print(f"Setting TTL for {key}")
                    self.redis.set_ttl(key, 3600)

                if request_data["request_method"] == "POST":
                    print(f"POST request detected: {key}.")
                    self.delete_old_requests(request_data["request_url"])
                    self.mark_related_get_as_refresh(request_data["request_url"])

                self.redis.increment_request_count(key)

                # Update cache with the analyzed request data
                self.llama.update_cache(request_data)

            except Exception as e:
                print(f"Error analyzing request {key}: {e}")

    def delete_old_requests(self, request_url):
        all_keys = self.redis.get_all_keys()
        newest_time = None
        newest_key = None

        for key in all_keys:
            request_data = self.redis.get_request_data(key)
            if request_data["request_url"] == request_url:
                request_time = float(request_data.get('last_used', 0))
                if newest_time is None or request_time > newest_time:
                    newest_time = request_time
                    newest_key = key

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
            if request_data["request_method"] == "GET" and self.compare_urls(request_data["request_url"], request_url):
                print(f"Marking GET request {key} as 'refresh' for URL {request_data['request_url']}")
                self.redis.client.hset(key, "purpose", "refresh")

    @staticmethod
    def compare_urls(url1, url2):
        return url1.lower() == url2.lower()  

    def run(self):
        while True:
            self.analyze_requests()
            time.sleep(600)  

# --------------- Multithreading Execution -----------------
def run_trainer():
    trainer = LlamaTrainer()
    trainer.run_training()

def run_analyzer():
    analyzer = RequestAnalyzer()
    analyzer.run()

if __name__ == "__main__":
    trainer_thread = threading.Thread(target=run_trainer)
    analyzer_thread = threading.Thread(target=run_analyzer)

    trainer_thread.start()
    analyzer_thread.start()

    trainer_thread.join()
    analyzer_thread.join()