import os
import requests

DATA_ENDPOINT = os.environ.get('DATA_ENDPOINT', 'http://localhost:20400')
print('DATA_ENDPOINT', DATA_ENDPOINT)

def download_data(body):
    response = requests.post(f'{DATA_ENDPOINT}/data/download', json=body)
    if response.status_code != 200:
        raise ValueError(response.text)
        raise ValueError(response.status_code)
    return response.json()