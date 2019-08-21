from flask_restplus import Resource, Namespace
import marshmallow
from webargs.flaskparser import use_args, use_kwargs

from ..model import utils_manager

api = Namespace('utils', description='Some utility functions')

@api.route('/unshorten')
class UrlUnshortener(Resource):
    args = {
        'url': marshmallow.fields.Str(required=True)
    }

    @api.param('url', 'The URL to unshorten')
    @use_kwargs(args)
    def get(self, url):
        if not url:
            return {'error': 'missing param url'}, 400
        unshortened = utils_manager.unshorten_url(url)

        return unshortened

@api.route('/time_published')
class TimePublished(Resource):
    args = {
        'url': marshmallow.fields.Str(missing=None)
    }

    @api.param('url', 'The URL to get the publishing time')
    @use_kwargs(args)
    def get(self, url):
        if not url:
            return {'error': 'missing param url'}, 400
        unshortened = utils_manager.get_url_published_time(url)

        return unshortened