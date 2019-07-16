### This package is the View part, interfacing with web requests
from flask_cors import CORS

from . import entity_views, static_resources, stats_views, analysis_views, utils_views, credibility_views
from . import static_resources

def configure_endpoints(app, api):
    base_url = '/misinfo'

    # endpoints for the entities
    api.add_resource(entity_views.Tweet, '/entities/tweets/<int:tweet_id>')
    api.add_resource(entity_views.TweetList, '/entities/tweets')
    api.add_resource(entity_views.TwitterAccount, '/entities/twitter_accounts/<int:account_id>')
    api.add_resource(entity_views.TwitterAccountList, '/entities/twitter_accounts')
    api.add_resource(entity_views.FactcheckingOrganisation, '/entities/factchecking_organisations/<string:org_id>')
    api.add_resource(entity_views.FactcheckingOrganisationList, '/entities/factchecking_organisations')
    api.add_resource(entity_views.FactcheckingReviewList, '/entities/factchecking_reviews')
    # endpoints for dataset stats
    api.add_resource(entity_views.DataStats, '/entities')
    api.add_resource(entity_views.DomainsStats, '/entities/domains')
    api.add_resource(entity_views.SourcesStats, '/entities/sources')
    api.add_resource(entity_views.FactcheckersTable, '/entities/factcheckers_table')

    # endpoints for the analyses
    api.add_resource(analysis_views.UrlAnalysis, '/analysis/urls')
    api.add_resource(analysis_views.TweetAnalysis, '/analysis/tweets')
    api.add_resource(analysis_views.TwitterAccountAnalysis, '/analysis/twitter_accounts')
    # time-related analyses
    api.add_resource(analysis_views.UrlTimeDistributionAnalysis, '/analysis/time_distribution_url')
    api.add_resource(analysis_views.TweetsTimeDistributionAnalysis, '/analysis/time_distribution_tweets')

    # endpoints for the credibility graph
    api.add_resource(credibility_views.CredibilitySource, '/credibility/sources/<string:source>')

    # endpoints for the stats
    api.add_resource(stats_views.TwitterAccountStats, '/stats/twitter_accounts')

    # endpoints for utils
    api.add_resource(utils_views.UrlUnshortener, '/utils/unshorten')
    api.add_resource(utils_views.TimePublished, '/utils/time_published')

    # endpoints for the static resources (frontend)
    static_resources.configure_static_resources(base_url, app)

def configure_cors(app):
    # define here rules for the CORS and endpoints. Remember that in deployment the requests come from the same domain
    cors = CORS(app, resources={r"/misinfo/api/*": {"origins": "*"}})
