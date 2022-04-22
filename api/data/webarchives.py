import re
import requests

from . import utils

def permacc_resolve_url(url):
    match = re.match(r'https?://(www\.)?perma\.cc/(?P<perma_id>[^/]+)', url)
    perma_id = match.group('perma_id')
    url = f'https://perma.cc/api/v1/public/archives/{perma_id}/?format=json'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    url_resolved = data['url']
    return url_resolved

def archiveorg_resolve_url(url):
    match = re.match(r'^https?:\/\/web\.archive\.org.*\/(?P<original>https?:\/\/.*)', url)
    original_url = match.group('original')
    return original_url

domains = {
    'perma.cc': permacc_resolve_url,
    'archive.org': archiveorg_resolve_url,
}

def resolve_url(url):
    domain = utils.get_url_domain(url)
    if domain not in domains:
        raise ValueError(f'Domain {domain} not supported by webarchives')
    return domains[domain](url)