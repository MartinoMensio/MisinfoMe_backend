# this endpoint is for the visualisation and interrogation of the credibility scores and graph
from flask_restplus import Resource, marshal_with, Namespace
import webargs
import marshmallow
import flask_restplus
from webargs.flaskparser import use_args, use_kwargs

from ..model import credibility_manager, jobs_manager
from .. import app

api = Namespace('credibility', description='Interfacing with the credibility component')


@api.route('/origins/')
@api.doc(description='Get the origins used to create the assessments')
class CredibilityOrigins(Resource):
    @api.response(200, 'Success')
    def get(self):
        return credibility_manager.get_credibility_origins()

@api.route('/factcheckers/')
@api.doc(description='Get the factcheckers from IFCN')
class CredibilityFactcheckers(Resource):
    @api.response(200, 'Success')
    def get(self):
        return credibility_manager.get_factcheckers()


@api.route('/sources/')
@api.param('source', 'The source is a domain name (e.g., `snopes.com`)')
@api.doc(description='Get the credibility of a certain source')
class SourceCredibility(Resource):
    @api.response(200, 'Success')
    @use_kwargs({'source': marshmallow.fields.Str(required=True)})
    @api.param('source', description='The source to analyse', required=True)
    def get(self, source):
        return credibility_manager.get_source_credibility(source)

    @use_kwargs({
        'source': marshmallow.fields.Str(required=True),
        'callback_url': marshmallow.fields.Str(missing=None)
    })
    @api.param('callback_url', description='The callback_url coming from the gateway. If absent, the call will be blocking', missing=None)
    @api.param('source', description='The source to analyse', required=True)
    def post(self, source, callback_url):
        """Endpoint for gateway"""
        if callback_url:
            return jobs_manager.create_task_for(credibility_manager.get_source_credibility, source, callback_url=callback_url)
        else:
            return credibility_manager.get_source_credibility(source)

@api.route('/urls/')
@api.param('url', 'The URL to be checked')
@api.doc(description='Get the credibility of a certain URL')
class UrlCredibility(Resource):
    @api.response(200, 'Success')
    @use_kwargs({'url': marshmallow.fields.Str(required=True)})
    @api.param('url', description='The URL to analyse', required=True)
    def get(self, url):
        return credibility_manager.get_url_credibility(url)

    @use_kwargs({
        'url': marshmallow.fields.Str(required=True),
        'callback_url': marshmallow.fields.Str(missing=None)
    })
    @api.param('callback_url', description='The callback_url coming from the gateway. If absent, the call will be blocking', missing=None)
    @api.param('url', description='The url to analyse', required=True)
    def post(self, url, callback_url):
        """Endpoint for gateway"""
        if callback_url:
            return jobs_manager.create_task_for(credibility_manager.get_url_credibility, url, callback_url=callback_url)
        else:
            return credibility_manager.get_url_credibility(url)

@api.route('/tweets/<int:tweet_id>')
@api.param('tweet_id', 'The tweet is a identified by its ID, of type `int`')
@api.doc(description='Get the credibility of a certain tweet')
class TweetCredibility(Resource):
    args = {
        'wait': marshmallow.fields.Boolean(missing=True)
    }

    args_post = {
        'callback_url': marshmallow.fields.Str(missing=None)
    }

    @use_kwargs(args)
    @api.param('wait', description='Do you want to be waiting, or get a work id that you can query later?', type=bool, missing=True)
    @api.response(200, 'Success')
    @api.response(422, 'Invalid tweet_id')
    @api.response(404, 'Tweet not found')
    def get(self, tweet_id, wait):
        print('wait', wait)
        if not wait:
            return jobs_manager.create_task_for(credibility_manager.get_tweet_credibility_from_id, tweet_id)
        else:
            result = credibility_manager.get_tweet_credibility_from_id(tweet_id)
            if not result:
                return {'error': 'Tweet not found'}, 404
            return result

    @use_kwargs(args_post)
    @api.param('callback_url', description='The callback_url coming from the gateway. If absent, the call will be blocking', missing=None)
    def post(self, tweet_id, callback_url):
        """Endpoint for gateway"""
        if callback_url:
            return jobs_manager.create_task_for(credibility_manager.get_tweet_credibility_from_id, tweet_id, callback_url=callback_url)
        else:
            return credibility_manager.get_tweet_credibility_from_id(tweet_id)

@api.route('/users/')
class TwitterUserCredibility(Resource):
    args = {
        'wait': marshmallow.fields.Boolean(missing=True),
        'screen_name': marshmallow.fields.Str(required=True)
    }
    args_post = {
        'screen_name': marshmallow.fields.Str(required=True),
        'callback_url': marshmallow.fields.Str(missing=None)
    }

    @use_kwargs(args)
    @api.param('wait', description='Do you want to be waiting, or get a work id that you can query later?', type=bool, missing=True)
    @api.param('screen_name', description='The `screen_name` of the twitter profile to analyse', required=True)
    #@api.doc(params={'screen_name': 'The screen_name of the twitter profile to analyse'})
    def get(self, screen_name, wait): #TODO TypeError: get() missing 1 required positional argument: 'screen_name'
        if not wait:
            return jobs_manager.create_task_for(credibility_manager.get_user_credibility_from_screen_name, screen_name)
        else:
            result = credibility_manager.get_user_credibility_from_screen_name(screen_name)
            if not result:
                return {'error': 'Tweets not found'}, 404
            return result

    @use_kwargs(args_post)
    @api.param('screen_name', description='The `screen_name` of the twitter profile to analyse', required=True)
    @api.param('callback_url', description='A URL to be POSTed with the result of the job. If absent, the call will be blocking', missing=None)
    def post(self, screen_name, callback_url):
        """Endpoint for gateway"""
        if callback_url:
            return jobs_manager.create_task_for(credibility_manager.get_user_credibility_from_screen_name, screen_name, callback_url=callback_url)
        else:
            return credibility_manager.get_user_credibility_from_screen_name(screen_name)

@api.route('/user-friends/')
class TwitterUserFriendsCredibility(Resource):
    args = {
        'screen_name': marshmallow.fields.Str(required=True),
        'limit': marshmallow.fields.Int(missing=300)
    }

    @use_kwargs(args)
    @api.param('screen_name', description='The `screen_name` of the twitter profile with the friends to get the cached analysis', required=True)
    @api.param('limit', description='How many friends to retrieve, default 300')
    def get(self, screen_name, limit):
        result = credibility_manager.get_user_friends_credibility_from_screen_name(screen_name, limit)
        return result
