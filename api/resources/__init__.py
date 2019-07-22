### This package is the View part, interfacing with web requests
import flask_restplus
import flask
from flask_cors import CORS

from . import entity_views, static_resources, stats_views, analysis_views, utils_views, credibility_views
from . import static_resources
from ..external import ExternalException



def configure_endpoints(app: flask.Flask, api: flask_restplus.Api):
    base_url = '/misinfo'

    @api.errorhandler(ExternalException)
    def default_error_handler(error: ExternalException):
        return error.json_error, error.status_code

    # endpoints for the entities
    api.add_namespace(entity_views.api)

    # endpoints for the analyses
    api.add_namespace(analysis_views.api)

    # endpoints for the credibility graph
    api.add_namespace(credibility_views.api)

    # endpoints for the stats
    api.add_namespace(stats_views.api)

    # endpoints for utils
    api.add_namespace(utils_views.api)

    # endpoints for the static resources (frontend)
    static_resources.configure_static_resources(base_url, app, api)

def configure_cors(app):
    # define here rules for the CORS and endpoints. Remember that in deployment the requests come from the same domain
    cors = CORS(app, resources={r"/misinfo/api/*": {"origins": "*"}})
