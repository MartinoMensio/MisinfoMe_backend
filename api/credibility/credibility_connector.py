import os
import requests

CREDIBILITY_ENDPOINT = os.environ.get('CREDIBILITY_ENDPOINT', 'http://localhost:8000')
print('CREDIBILITY_ENDPOINT', CREDIBILITY_ENDPOINT)

def get_source_credibility(source):
    response = requests.get(f'{CREDIBILITY_ENDPOINT}/sources/{source}')
    if response.status_code != 200:
        raise ValueError(response.status_code)
    return response.json()
