from flask_restplus import Resource, marshal_with, Namespace

from ..model import jobs_manager

api = Namespace('jobs', description='Get the results of the jobs')


@api.route('/status/<task_id>')
@api.doc(description='Get the statuses of the jobs')
class JobStatus(Resource):
    @api.response(200, 'Success')
    def get(self, task_id):
        return jobs_manager.get_task_status(task_id)

@api.route('/status_by_query_id/<query_id>')
@api.doc(description='Get the statuses of the job from the query_id')
class JobStatusFromQueryId(Resource):
    @api.response(200, 'Success')
    def get(self, query_id):
        return jobs_manager.get_task_status_from_query_id(query_id)
