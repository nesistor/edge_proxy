import http.server
import socketserver
import json
import os
import requests
import sqlite3
from urllib.parse import urlparse, urlunparse
from transformers import LlamaTokenizer, LlamaForCausalLM

# Path to the LLaMA model and the database
MODEL_DIR = "path_to_llama_model"  # Change to the appropriate path
DATABASE = "proxy_cache.db"

# Initialization of the LLaMA model
tokenizer = LlamaTokenizer.from_pretrained(MODEL_DIR)
model = LlamaForCausalLM.from_pretrained(MODEL_DIR)

# Function to initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache (
            url TEXT PRIMARY KEY,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Function to save data to cache
def save_to_cache(url, response):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO cache (url, response) VALUES (?, ?)
    ''', (url, response))
    conn.commit()
    conn.close()

# Function to retrieve data from cache
def get_from_cache(url):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT response FROM cache WHERE url = ?', (url,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# Function to analyze a request using the LLaMA model
def analyze_with_llama(request_text):
    inputs = tokenizer(request_text, return_tensors="pt")
    outputs = model.generate(**inputs)
    response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response_text

# Function to fetch data from the appropriate API
def fetch_data_from_api(url, headers=None):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json(), response.headers
        elif response.status_code == 304:
            return None, response.headers
        else:
            return None, None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None, None

# Proxy server that dynamically handles requests to multiple APIs
class ProxyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Capture the full URL of the request
        parsed_url = urlparse(self.path)
        full_url = urlunparse(('http', parsed_url.netloc, parsed_url.path, '', parsed_url.query, ''))

        # Analyze the request with the LLaMA model
        analyzed_request = analyze_with_llama(f"Analyze the following request: {full_url}")

        # Check if the data is already in cache
        cached_response = get_from_cache(full_url)

        if cached_response:
            # If the data is in cache, return it
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(json.loads(cached_response)).encode('utf-8'))
        else:
            # If no data in cache, fetch it from the API
            api_response, headers = fetch_data_from_api(full_url)
            
            if api_response:
                # Update the cache with the data from the API
                save_to_cache(full_url, json.dumps(api_response))

                # Return the API data to the client
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(api_response).encode('utf-8'))
            else:
                # If the data is not available, return an error
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Error fetching data from API")

# Run the proxy server
def run_proxy_server(port=8080):
    handler = ProxyRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Proxy server running on port {port}")
        httpd.serve_forever()

if __name__ == "__main__":
    init_db()  # Initialize the database
    run_proxy_server(port=8080)
