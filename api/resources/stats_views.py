from flask_restful import Resource
from webargs import fields
from webargs.flaskparser import use_args, use_kwargs

from ..model import stats_manager

class TwitterAccountStats(Resource):
    def get(self):
        accounts_stats = stats_manager.get_overall_counts()

        return accounts_stats