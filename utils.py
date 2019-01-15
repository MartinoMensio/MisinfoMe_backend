import json
from urllib.parse import urlparse
import tldextract

def get_url_domain(url):
    #parsed_uri = urlparse(url)
    #return str(parsed_uri.netloc)
    ext = tldextract.extract(url)
    result = '.'.join(part for part in ext if part)
    return result.lower()

def get_url_domain_without_subdomains(url):
    ext = tldextract.extract(url)
    result = '{}.{}'.format(ext[1], ext[2])
    return result.lower()

def read_json(input_path):
    with open(input_path) as f:
        return json.load(f)