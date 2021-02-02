import os
import requests

CREDIBILITY_ENDPOINT = os.environ.get('CREDIBILITY_ENDPOINT', 'http://localhost:20300')
print('CREDIBILITY_ENDPOINT', CREDIBILITY_ENDPOINT)

def get_url_credibility(url):
    response = requests.get(f'{CREDIBILITY_ENDPOINT}/urls/', params={'url': url})
    if response.status_code != 200:
        raise ValueError(response.text)
        raise ValueError(response.status_code)
    return response.json()

def post_url_credibility_multiple(urls):
    response = requests.post(f'{CREDIBILITY_ENDPOINT}/urls/', json={'urls': urls})
    if response.status_code != 200:
        raise ValueError(response.status_code)
    return response.json()

def get_source_credibility(source):
    response = requests.get(f'{CREDIBILITY_ENDPOINT}/sources/', params={'source': source})
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

def get_factcheckers():
    response = requests.get(f'{CREDIBILITY_ENDPOINT}/factcheckers/')
    if response.status_code != 200:
        raise ValueError(response.status_code)
    return response.json()

def get_status():
    try:
        response = requests.get(f'{CREDIBILITY_ENDPOINT}/utils/status')
    except:
        return {
            'status': 'dead'
        }
    if response.status_code != 200:
        return {
            'status': f'HTTP code {response.status_code}'
        }
    return response.json()
