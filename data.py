import json
import copy
from urllib.parse import urlparse
from pathlib import Path

import database

def load_data(path_str='.'):
    path = Path(path_str)
    with open(path / 'aggregated_urls.json') as f:
        urls = json.load(f)
    with open(path / 'aggregated_domains.json') as f:
        domains = json.load(f)
    with open(path / 'aggregated_rebuttals.json') as f:
        rebuttals = json.load(f)
    return {
        'by_url': urls,
        'by_domain': domains,
        'rebuttals': rebuttals
    }

def classify_url(url_info):
    url = url_info['resolved']
    label = database.get_url_info(url)
    if label:
        label['reason'] = 'full URL match'
        label['url'] = url
    else:
        domain = get_url_domain(url)
        label = database.get_domain_info(domain)
        if not label and domain.startswith('www.'):
            # try also without www.
            label = database.get_domain_info(domain[4:])
        if label:
            label['reason'] = 'domain match'
            label['url'] = url
    if label:
        label['found_in_tweet'] = url_info['found_in_tweet']
        label['retweet'] = url_info['retweet']
        #print(label)
    return label

def get_url_domain(url):
    parsed_uri = urlparse(url)
    return parsed_uri.netloc
