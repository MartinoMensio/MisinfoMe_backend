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

@api.route('/analysis/')
@api.doc(description='Analyse a profile')
class FrontendV2Analysis(Resource):
    args = {
        'screen_name': marshmallow.fields.String(required=True),
        'wait': marshmallow.fields.Bool(missing=False)
    }

    @api.response(200, 'Success')
    @use_kwargs(args)
    @api.param('screen_name', description='The screen name of the profile to be analysed', type=str, required=True)
    @api.param('wait', description='Do you want to wait or to use job manager?', type=bool, missing=False)
    def post(self, screen_name, wait):
        print(wait)
        if not wait:
            return jobs_manager.create_task_for(credibility_manager.get_v2_profile_credibility, screen_name)
        else:
            return credibility_manager.get_v2_profile_credibility(screen_name)
    
    @api.response(200, 'Success')
    @use_kwargs(args)
    @api.param('screen_name', description='The screen name of the profile to be analysed', type=str, required=True)
    @api.param('wait', description='Do you want to wait or to use job manager?', type=bool, missing=False)
    def get(self, screen_name, wait):
        print(wait)
        if not wait:
            return jobs_manager.create_task_for(credibility_manager.get_v2_profile_credibility, screen_name)
        else:
            return credibility_manager.get_v2_profile_credibility(screen_name)

