import os
import requests

CREDIBILITY_ENDPOINT = os.environ.get('CREDIBILITY_ENDPOINT', 'http://localhost:20300')
print('CREDIBILITY_ENDPOINT', CREDIBILITY_ENDPOINT)

def get_source_credibility(source):
    response = requests.get(f'{CREDIBILITY_ENDPOINT}/sources/{source}')
    if response.status_code != 200:
        raise ValueError(response.status_code)
    return response.json()

def post_source_credibility_multiple(sources):
    response = requests.post(f'{CREDIBILITY_ENDPOINT}/sources/', json={'sources': sources})
    if response.status_code != 200:
        raise ValueError(response.status_code)
    return response.json()

def get_origins():
    response = requests.get(f'{CREDIBILITY_ENDPOINT}/origins/')
    if response.status_code != 200:
        raise ValueError(response.status_code)
    return response.json()
