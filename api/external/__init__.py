import requests
from fastapi import HTTPException

class ExternalException(HTTPException):
    """An helper to propagate the error when the other services provide a bad answer"""

    def __init__(self, response: requests.Response):
        error_json = {
            "response": response.json(),
            "http_status_code": response.status_code,
            "originating_url": response.url,
            "originating_method": response.request.method
        }
        super().__init__(response.status_code, error_json)
