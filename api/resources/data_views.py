# this endpoint is for updating the datasets
from flask_restplus import Resource, marshal_with, Namespace
import webargs
import marshmallow
import flask_restplus
from flask import request
from webargs.flaskparser import use_args, use_kwargs

from ..external import claimreview_scraper_connector, credibility_connector
from .. import app

api = Namespace('data', description='Update data collection')

@api.route('/update/')
@api.doc(description='Update the dataset from GitHub')
class CredibilityOrigins(Resource):
    @api.response(200, 'Success')
    def post(self):
        json_data = request.json
        print(json_data)
        a = credibility_connector.update_origin('ifcn')
        print(a)
        b = claimreview_scraper_connector.download_data(json_data)
        print(b)
        c = credibility_connector.update_origin('factchecking_report')
        print(c)
        return b
        
@api.route('/latest/')
@api.doc(description='Get the latest data release')
class LatestData(Resource):
    args = {
        'file_name': marshmallow.fields.Str(missing=None)
    }
    @use_kwargs(args)
    @api.param('file_name', 'The wanted file. Use the keys from the "files" dict that you can get without this parameter')
    @api.response(200, 'Success')
    def get(self, file_name):
        return claimreview_scraper_connector.get_latest(file_name)

@api.route('/sample/')
@api.doc(description='Get random data samples')
class RandomSamples(Resource):
    args = {
        'since': marshmallow.fields.Str(missing=None),
        'until': marshmallow.fields.Str(missing=None),
        'misinforming_domain': marshmallow.fields.Str(missing=None),
        'fact_checker_domain': marshmallow.fields.Str(missing=None),
        'exclude_twitter_misinfo': marshmallow.fields.Bool(missing=True),
        'cursor': marshmallow.fields.Str(missing=None),
    }
    @use_args(args)
    @api.param('since', 'Time filter, only get items published since the provided date. Format YYYY-MM-DD')
    @api.param('until', 'Time filter, only get items published until the provided date. Format YYYY-MM-DD')
    @api.param('misinforming_domain', 'The domain where misinformation is published, e.g., breitbart.com')
    @api.param('fact_checker_domain', 'The domain of the factchecker, e.g., snopes.com')
    @api.param('exclude_twitter_misinfo', 'Whether to exclude fact-checked links to twitter.com. Default is true. It will be discarded if `misinforming_domain` is equal to `twitter.com`')
    @api.param('cursor', 'The cursor to resume sampling')
    @api.response(200, 'Success')
    def get(self, args):
        print(args)
        return claimreview_scraper_connector.get_sample(args)


