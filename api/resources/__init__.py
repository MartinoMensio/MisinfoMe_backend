### This package is the View part, interfacing with web requests
import flask_restplus
import flask
from flask_cors import CORS

from . import entity_views, static_resources, stats_views, analysis_views, utils_views, credibility_views
from . import static_resources



def configure_endpoints(app: flask.Flask, api: flask_restplus.Api):
    credibility_views.global_api = api
    base_url = '/misinfo'

    # endpoints for the entities
    entities_ns = api.namespace('entities', description='Basic entities stored in the service')
    #entities_ns.add_resource(entity_views.Tweet, '/tweets/<int:tweet_id>')
    #entities_ns.add_resource(entity_views.TweetList, '/tweets')
    #entities_ns.add_resource(entity_views.TwitterAccount, '/twitter_accounts/<int:account_id>')
    #entities_ns.add_resource(entity_views.TwitterAccountList, '/twitter_accounts')
    #entities_ns.add_resource(entity_views.TwitterFriends, '/search/friends')
    entities_ns.add_resource(entity_views.FactcheckingOrganisation, '/factchecking_organisations/<string:org_id>')
    entities_ns.add_resource(entity_views.FactcheckingOrganisationList, '/factchecking_organisations')
    entities_ns.add_resource(entity_views.FactcheckingReviewList, '/factchecking_reviews')
    # endpoints for dataset stats
    entities_ns.add_resource(entity_views.DataStats, '/')
    entities_ns.add_resource(entity_views.DomainsStats, '/domains')
    entities_ns.add_resource(entity_views.OriginsStats, '/origins')
    entities_ns.add_resource(entity_views.FactcheckersTable, '/factcheckers_table')

    # endpoints for the analyses
    analysis_ns = api.namespace('analysis', description='Analysis of some entities')
    analysis_ns.add_resource(analysis_views.UrlAnalysis, '/urls')
    analysis_ns.add_resource(analysis_views.TweetAnalysis, '/tweets')
    analysis_ns.add_resource(analysis_views.TwitterAccountAnalysis, '/twitter_accounts')
    # time-related analyses
    analysis_ns.add_resource(analysis_views.UrlTimeDistributionAnalysis, '/time_distribution_url')
    analysis_ns.add_resource(analysis_views.TweetsTimeDistributionAnalysis, '/time_distribution_tweets')

    # endpoints for the credibility graph
    api.add_namespace(credibility_views.api)

    # endpoints for the stats
    stats_ns = api.namespace('stats', description='Some statistics')
    stats_ns.add_resource(stats_views.TwitterAccountStats, '/twitter_accounts')

    # endpoints for utils
    utils_ns = api.namespace('utils', description='Some utility functions')
    utils_ns.add_resource(utils_views.UrlUnshortener, '/unshorten')
    utils_ns.add_resource(utils_views.TimePublished, '/time_published')

    # endpoints for the static resources (frontend)
    static_resources.configure_static_resources(base_url, app, api)

def configure_cors(app):
    # define here rules for the CORS and endpoints. Remember that in deployment the requests come from the same domain
    cors = CORS(app, resources={r"/misinfo/api/*": {"origins": "*"}})
