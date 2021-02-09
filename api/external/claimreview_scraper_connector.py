import os
import requests
from io import BytesIO
from flask import send_file

DATA_ENDPOINT = os.environ.get('DATA_ENDPOINT', 'http://localhost:20400')
print('DATA_ENDPOINT', DATA_ENDPOINT)

def download_data(body):
    response = requests.post(f'{DATA_ENDPOINT}/data/download', json=body)
    if response.status_code != 200:
        raise ValueError(response.text)
    return response.json()

def get_latest(file_name):
    params = {}
    if file_name:
        params['file'] = file_name
    response = requests.get(f'{DATA_ENDPOINT}/data/daily/latest', params=params)
    if response.status_code != 200:
        raise ValueError(response.text)

    if not file_name:
        return response.json()
    else:
        # binary file
        file_name = response.headers['content-disposition'].replace('attachment', '').replace(';', '').replace('filename=', '').replace('"', '').strip()
        file = BytesIO(response.content)
        file.seek(0)
        return send_file(file, attachment_filename=file_name, as_attachment=True)

def get_sample(args):
    response = requests.get(f'{DATA_ENDPOINT}/data/sample', params=args)
    if response.status_code != 200:
        raise ValueError(response.text)
    return response.json()