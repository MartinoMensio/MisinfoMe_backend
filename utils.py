import json
from urllib.parse import urlparse

def get_url_domain(url):
    parsed_uri = urlparse(url)
    return str(parsed_uri.netloc)

def read_json(input_path):
    with open(input_path) as f:
        return json.load(f)