import json
from urllib.parse import urlparse
from pathlib import Path

def load_data(path_str='.'):
    path = Path(path_str)
    with open(path / 'aggregated_urls.json') as f:
        urls = json.load(f)
    with open(path / 'aggregated_domains.json') as f:
        domains = json.load(f)
    return {
        'by_url': urls,
        'by_domain':domains
    }

def classify_url(url_info, data):
    url = url_info['resolved']
    label = data['by_url'].get(url, None)
    if label:
        label['reason'] = 'The URL you shared matched'
    else:
        domain = get_url_domain(url)
        label = data['by_domain'].get(domain, None)
        if label:
            label['reason'] = 'The domain of the URL you shared matched'
            label['url'] = url
    if label:
        label['found_in_tweet'] = url_info['found_in_tweet']
    return label

def get_url_domain(url):
    parsed_uri = urlparse(url)
    return parsed_uri.netloc
