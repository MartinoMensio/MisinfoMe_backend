# this endpoint is for the visualisation and interrogation of the credibility scores and graph
from flask_restplus import Resource, marshal_with, Namespace
import webargs
import marshmallow
import flask_restplus
from webargs.flaskparser import use_args, use_kwargs

from ..external import twitter_connector
from .. import app

api = Namespace('twitter', description='Interfacing with the twitter connector')


@api.route('/tweets/<int:tweet_id>')
@api.doc(description='Get the origins used to create the assessments')
class CredibilityOrigins(Resource):
    @api.response(200, 'Success')
    def get(self, tweet_id):
        return twitter_connector.get_tweet(tweet_id)