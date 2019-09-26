from flask_restplus import Resource, marshal_with, Namespace
from webargs.flaskparser import use_kwargs
import marshmallow

from ..model import jobs_manager

api = Namespace('jobs', description='Query the status of the jobs')


@api.route('/status/<job_id>')
@api.doc(description='Get the statuses of the jobs')
class JobStatus(Resource):
    @api.response(200, 'Success')
    def get(self, job_id):
        return jobs_manager.get_task_status(job_id)

@api.route('/status_by_callback_url')
@api.doc(description='Get the statuses of the job from the callback_url')
class JobStatusFromCallbackUrl(Resource):

    @use_kwargs({
        'callback_url': marshmallow.fields.Str(required=True)
    })
    @api.param('callback_url', description='The callback_url that was sent from the gateway', required=True)
    @api.response(200, 'Success')
    def get(self, callback_url):
        return jobs_manager.get_task_status_from_callback_url(callback_url)
