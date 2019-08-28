from flask_restplus import Resource, Namespace
from webargs import fields
import marshmallow
from webargs.flaskparser import use_args, use_kwargs

from ..model import stats_manager

api = Namespace('stats', description='Some statistics')

@api.route('/twitter_accounts')
class TwitterAccountStats(Resource):

    args = {
        'use_credibility': marshmallow.fields.Boolean(missing=False)
    }

    @use_kwargs(args)
    @api.param('use_credibility', 'Wether to use the old model (false) or the new one based on credibility (legacy data interface as the old model)')
    def get(self, use_credibility):
        accounts_stats = stats_manager.get_overall_counts(use_credibility)

        return accounts_stats