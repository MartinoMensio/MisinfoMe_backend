import json
from urllib.parse import urlparse
from pathlib import Path

def load_data(path_str='.'):
    path = Path(path_str)
    with open(path / 'all_urls.json') as f:
        urls = json.load(f)
    with open(path / 'all_domains.json') as f:
        domains = json.load(f)
    return {
        'by_url': {el['url']: el for el in urls},
        'by_domain': {el['domain']: el for el in domains}
    }

def classify_url(url, data):
    label = data['by_url'].get(url, None)
    if label:
        label['reason'] = 'The URL you shared matched'
    else:
        domain = get_url_domain(url)
        label = data['by_domain'].get(domain, None)
        if label:
            label['reason'] = 'The domain of the URL you shared matched'
            label['url'] = url
    return label

def get_url_domain(url):
    parsed_uri = urlparse(url)
    return parsed_uri.netloc
