class ExternalException(Exception):
    """An helper to propagate the error when the other services provide a bad answer"""

    status_code: int
    json_error: dict

    def __init__(self, status_code: int, json_error: dict):
        self.status_code = status_code
        self.json_error = json_error
