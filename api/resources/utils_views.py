from flask_restful import Resource
import marshmallow
from webargs.flaskparser import use_args, use_kwargs

from ..model import utils_manager

class UrlUnshortener(Resource):
    args = {
        'url': marshmallow.fields.Str(missing=None)
    }

    @use_kwargs(args)
    def get(self, url):
        if not url:
            return {'error': 'missing param url'}, 400
        unshortened = utils_manager.unshorten_url(url)

        return unshortened

class TimePublished(Resource):
    args = {
        'url': marshmallow.fields.Str(missing=None)
    }

    @use_kwargs(args)
    def get(self, url):
        if not url:
            return {'error': 'missing param url'}, 400
        unshortened = utils_manager.get_url_published_time(url)

        return unshortened