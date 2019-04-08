### This package is the View part, interfacing with web requests
from flask_cors import CORS

from . import entity_views, static_resources, stats_views, analysis_views, utils_views
from . import static_resources

def configure_endpoints(app, api):
    base_url = '/misinfo'
    api_url = base_url + '/api'

    # endpoints for the entities
    api.add_resource(entity_views.Tweet, api_url + '/entities/tweets/<int:tweet_id>')
    api.add_resource(entity_views.TweetList, api_url + '/entities/tweets')
    api.add_resource(entity_views.TwitterAccount, api_url + '/entities/twitter_accounts/<int:account_id>')
    api.add_resource(entity_views.TwitterAccountList, api_url + '/entities/twitter_accounts')
    api.add_resource(entity_views.FactcheckingOrganisation, api_url + '/entities/factchecking_organisations/<string:org_id>')
    api.add_resource(entity_views.FactcheckingOrganisationList, api_url + '/entities/factchecking_organisations')

    # endpoints for the analyses
    # TODO
    api.add_resource(analysis_views.UrlAnalysis, api_url + '/analysis/urls')
    api.add_resource(analysis_views.TweetAnalysis, api_url + '/analysis/tweets')
    api.add_resource(analysis_views.TwitterAccountAnalysis, api_url + '/analysis/twitter_accounts')
    #api.add_resource(analysis_views.TwitterAccountAnalysis, api_url + '/analysis/twitter_accounts/<int:user_id>', endpoint='twitteraccountanalysis1')

    # endpoints for the stats
    api.add_resource(stats_views.TwitterAccountStats, api_url + '/stats/twitter_accounts')

    # endpoints for utils
    api.add_resource(utils_views.UrlUnshortener, api_url + '/utils/unshorten')
    api.add_resource(utils_views.TimePublished, api_url + '/utils/time_published')

    # endpoints for the static resources (frontend)
    static_resources.configure_static_resources(base_url, app)

def configure_cors(app):
    # define here rules for the CORS and endpoints. Remember that in deployment the requests come from the same domain
    cors = CORS(app, resources={r"/misinfo/api/*": {"origins": "*"}})
