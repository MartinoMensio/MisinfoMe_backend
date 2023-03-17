from flask_restplus import Resource, marshal_with, Namespace
import flask_restplus
import webargs
import marshmallow
from webargs.flaskparser import use_args, use_kwargs

from ..model import jobs_manager
from ..model import credibility_manager
from ..model import entity_manager
from . import statuses

api = Namespace('frontend/v2', description='The API for frontend v2 of MisinfoMe')

@api.route('/home/')
@api.doc(description='Get the info to populate the homepage')
class FrontendV2Home(Resource):
    @api.response(200, 'Success')
    def get(self):
        return entity_manager.get_frontend_v2_home()

@api.route('/home/most_popular_entries')
@api.doc(description='Get the most searched profiles')
class FrontendV2HomePopularEntries(Resource):
    @api.response(200, 'Success')
    def get(self):
        return entity_manager.get_most_popular_entries()

@api.route('/profiles/')
@api.doc(description='Analyse a profile')
class FrontendV2Analysis(Resource):
    args = {
        'screen_name': marshmallow.fields.String(required=True),
        'until_id': marshmallow.fields.String(missing=None),
        'wait': marshmallow.fields.Bool(missing=False)
    }

    @api.response(200, 'Success')
    @use_kwargs(args)
    @api.param('screen_name', description='The screen name of the profile to be analysed', type=str, required=True)
    @api.param('until_id', description='To continue previous analysis', type=str, missing=None)
    @api.param('wait', description='Do you want to wait or to use job manager?', type=bool, missing=False)
    def post(self, screen_name, until_id, wait):
        print(wait)
        if not wait:
            return jobs_manager.create_task_for(credibility_manager.get_v2_profile_credibility, screen_name, until_id)
        else:
            return credibility_manager.get_v2_profile_credibility(screen_name, until_id)
    
    @api.response(200, 'Success')
    @use_kwargs(args)
    @api.param('screen_name', description='The screen name of the profile to be analysed', type=str, required=True)
    @api.param('until_id', description='To continue previous analysis', type=str, missing=None)
    @api.param('wait', description='Do you want to wait or to use job manager?', type=bool, missing=False)
    def get(self, screen_name, until_id, wait):
        print(wait)
        if not wait:
            return jobs_manager.create_task_for(credibility_manager.get_v2_profile_credibility, screen_name, until_id)
        else:
            return credibility_manager.get_v2_profile_credibility(screen_name, until_id)


# TODO add endpoint to analyse single tweet
@api.route('/tweets/<int:tweet_id>')
@api.param('tweet_id', 'The tweet is a identified by its ID, of type `int`')
@api.doc(description='Get the credibility of a certain tweet')
class TweetCredibilityV2(Resource):
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
