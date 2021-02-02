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
@api.doc(description='Get the origins used to create the assessments')
class CredibilityOrigins(Resource):
    @api.response(200, 'Success')
    def post(self):
        json_data = request.json
        print(json_data)
        return claimreview_scraper_connector.download_data(json_data)
