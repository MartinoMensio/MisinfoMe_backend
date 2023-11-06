import os
from fastapi import Response, HTTPException
import requests

from . import ExternalException

DATA_ENDPOINT = os.environ.get("DATA_ENDPOINT", "http://localhost:20400")
print("DATA_ENDPOINT", DATA_ENDPOINT)


def download_data(date):
    print(date)
    response = requests.post(f"{DATA_ENDPOINT}/data/download", json={"date": date})
    if response.status_code != 200:
        raise ExternalException(response.status_code, response.json())
    return response.json()


def get_latest(file_name):
    params = {}
    if file_name:
        params["file"] = file_name
    response = requests.get(f"{DATA_ENDPOINT}/data/daily/latest", params=params)
    if response.status_code != 200:
        raise ExternalException(response.status_code, response.json())

    if not file_name:
        return response.json()
    else:
        # binary file
        file_name = (
            response.headers["content-disposition"]
            .replace("attachment", "")
            .replace(";", "")
            .replace("filename=", "")
            .replace('"', "")
            .strip()
        )
        file_bytes = response.content
        content_type = response.headers["content-type"]
        if file_name == "zip":
            # TODO: openapi docs is not displaying download button
            content_type = "application/x-zip-compressed"
        return Response(content=file_bytes, media_type=content_type)


def get_sample(args):
    args = {k: v for k, v in args.items() if v != None and v != ""}
    response = requests.get(f"{DATA_ENDPOINT}/data/sample", params=args)
    if response.status_code != 200:
        raise HTTPException(response.status_code, response.json())
    return response.json()


def get_latest_factchecks():
    response = requests.get(f"{DATA_ENDPOINT}/data/latest_factchecks")
    if response.status_code != 200:
        raise ExternalException(response.status_code, response.json())
    return response.json()
