import os
import requests
from flask import Flask, Blueprint, request
try: 
    from flask_restplus import Api
except ImportError:
    import werkzeug, flask.scaffold
    werkzeug.cached_property = werkzeug.utils.cached_property
    flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func
    import collections
    collections.MutableMapping = collections.abc.MutableMapping
    from flask_restplus import Api
from flask.json import JSONEncoder
import datetime
import flask_monitoringdashboard as dashboard
from dotenv import load_dotenv
load_dotenv()

from . import resources

app = Flask(__name__)
app.url_map.strict_slashes = False


blueprint_api = Blueprint('api', __name__, url_prefix='/misinfo/api')

api = Api(blueprint_api)

app.register_blueprint(blueprint_api)

resources.configure_endpoints(app, api)
resources.configure_cors(app)

# dashboard to analyse the API usage
dashboard.config.link = 'misinfo/api/dashboard'
dashboard.config.password = os.environ['DASHBOARD_PASSWORD']
dashboard.bind(app)

# logging to Analytics
logging_enabled = os.environ.get('LOGGING_ENABLED', False) == 'yes'
@app.after_request
def after_request(response):
    if not logging_enabled:
        return response
    #print('after_request', request.remote_addr, request.method, request.scheme, request.full_path, response.status)
    try:
        data = {
            'v': '1',  # API Version.
            'tid': 'UA-143815717-1',  # Tracking ID / Property ID.
            'cid': 666, # client identifier
            't': 'event',  # Event hit type.
            'ec': 'backend_call',  # Event category.
            'ea': f'{request.method} {request.full_path}',  # Event action.
            'el': request.full_path,  # Event label.
            'ev': response.status_code,  # Event value, must be an integer
            'dp': request.full_path # where the event happened
        }
        headers = {
            'User-Agent': 'PostmanRuntime/7.19.0',
            'Accept': '*'
        }

        analytics_response = requests.get(
            'https://www.google-analytics.com/r/collect', params=data, headers=headers)
        #print(analytics_response.url)
        
        #print('analytics_response', analytics_response.status_code)

    except Exception as e:
        print(e)
    return response
