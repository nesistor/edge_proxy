import json

def format_request_data(request_data):
    return json.dumps(request_data, indent=2)
