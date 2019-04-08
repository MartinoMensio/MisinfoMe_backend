from flask import Flask, Blueprint
from flask_restplus import Api
from flask.json import JSONEncoder
import datetime

from . import resources

app = Flask(__name__)
app.url_map.strict_slashes = False


blueprint_api = Blueprint('api', __name__, url_prefix='/misinfo/api')

api = Api(blueprint_api)

app.register_blueprint(blueprint_api)

resources.configure_endpoints(app, api)
resources.configure_cors(app)
