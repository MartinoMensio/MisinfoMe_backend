# this endpoint is for updating the datasets
from flask_restplus import Resource, marshal_with, Namespace
import webargs
import marshmallow
import flask_restplus
from flask import request
from webargs.flaskparser import use_args, use_kwargs

from ..external import claimreview_scraper_connector
from .. import app

api = Namespace('data', description='Update data collection')

@api.route('/update/')
@api.doc(description='Update the dataset from GitHub')
class CredibilityOrigins(Resource):
    @api.response(200, 'Success')
    def post(self):
        json_data = request.json
        print(json_data)
        return claimreview_scraper_connector.download_data(json_data)
        
@api.route('/latest/')
@api.doc(description='Get the latest data release')
class CredibilityOrigins(Resource):
    args = {
        'file_name': marshmallow.fields.Str(missing=None)
    }
    @use_kwargs(args)
    @api.param('file_name', 'The wanted file. Use the keys from the "files" dict that you can get without this parameter')
    @api.response(200, 'Success')
    def get(self, file_name):
        return claimreview_scraper_connector.get_latest(file_name)
