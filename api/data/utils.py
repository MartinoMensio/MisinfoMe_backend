import json
from urllib.parse import urlparse
import tldextract
import re

def add_protocol(url):
    """when the URL does not have http://"""
    if not re.match(r'[a-z]+://.*', url):
        # default protocol
        url = 'https://' + url
    return url

def get_url_domain(url):
    #parsed_uri = urlparse(url)
    #return str(parsed_uri.netloc)
    if not url:
        return ''
    try:
        ext = tldextract.extract(url)
    except Exception:
        raise ValueError(url)
    result = '.'.join(part for part in ext if part)
    return result.lower()

def get_url_domain_without_www(url):
    result = get_url_domain(url)
    if result.startswith('www.'):
        result = result[4:]
    return result

def get_url_domain_without_subdomains(url):
    ext = tldextract.extract(url)
    result = '{}.{}'.format(ext[1], ext[2])
    return result.lower()

def read_json(input_path):
    with open(input_path) as f:
        return json.load(f)