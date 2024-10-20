import torch
from transformers import pipeline

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
        conversation = [
            {"role": "system", "content": "You are a request analysis assistant."},
            {"role": "user", "content": f"Analyze the following request: {request_data}"}
        ]
        output = self.pipe(conversation, max_new_tokens=150)
        return output[0]['generated_text']
