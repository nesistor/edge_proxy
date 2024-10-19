from transformers import pipeline

class LlamaModel:
    def __init__(self):
        model_id = 'meta-llama/Llama-3.2-1B-Instruct'
        self.pipe = pipeline('text-generation', model=model_id)

    def determine_ttl(self, request_data):
        # Użycie modelu LLaMA do wygenerowania TTL
        conversation = [
            {"role": "system", "content": "You are a helpful assistant analyzing web requests."},
            {"role": "user", "content": f"Analyze the following request: {request_data}"}
        ]

        response = self.pipe(conversation, max_new_tokens=64)
        model_output = response[0]['generated_text']

        # Na podstawie odpowiedzi modelu, ustaw TTL (można dodać logikę do wyciągania TTL)
        return 72 * 3600  # Domyślnie zwracamy 72 godziny
