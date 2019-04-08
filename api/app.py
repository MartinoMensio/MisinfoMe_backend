from flask import Flask
from flask_restful import Api

from . import resources

app = Flask(__name__)
app.url_map.strict_slashes = False
api = Api(app)

resources.configure_endpoints(app, api)
resources.configure_cors(app)
