# this endpoint is for the visualisation and interrogation of the credibility scores and graph
from flask_restplus import Resource, marshal_with, Namespace
import webargs
import marshmallow
import flask_restplus
from webargs.flaskparser import use_args, use_kwargs

from ..model import credibility_manager

api = Namespace('credibility', description='Interfacing with the credibility component')


@api.route('/sources/<string:source>')
@api.param('source', 'The source is a domain name (e.g., `snopes.com`)')
@api.doc(description='Get the credibility of a certain source')
class SourceCredibility(Resource):
    @api.response(200, 'Success')
    def get(self, source):
        return credibility_manager.get_source_credibility(source)

@api.route('/tweets/<int:tweet_id>')
@api.param('tweet_id', 'The tweet is a identified by its ID, of type `int`')
@api.doc(description='Get the credibility of a certain tweet')
class TweetCredibility(Resource):
    @api.response(200, 'Success')
    @api.response(422, 'Invalid tweet_id')
    @api.response(404, 'Tweet not found')
    def get(self, tweet_id):
        result = credibility_manager.get_tweet_credibility_from_id(tweet_id)
        if not result:
            return {'error': 'Tweet not found'}, 404
        return result

@api.route('/users/')
class TwitterUserCredibility(Resource):
    @use_kwargs({'screen_name': marshmallow.fields.Str(required=True)})
    @api.param('screen_name', description='The `screen_name` of the twitter profile to analyse', required=True)
    #@api.doc(params={'screen_name': 'The screen_name of the twitter profile to analyse'})
    def get(self, screen_name): #TODO TypeError: get() missing 1 required positional argument: 'screen_name'
        result = credibility_manager.get_user_credibility_from_screen_name(screen_name)
        if not result:
            return {'error': 'Tweets not found'}, 404
        return result
