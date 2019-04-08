from flask_restful import Resource
import webargs
import marshmallow
from webargs.flaskparser import use_args, use_kwargs

from ..model import entity_manager
from . import statuses


class Tweet(Resource):
    def get(self, tweet_id):
        tweet = entity_manager.get_tweet_from_id(tweet_id)
        if tweet:
            return tweet
        # TODO use twitter.def get_statuses_lookup(self, tweet_ids), use correct status codes for get old and retrieve new
        return {'error': 'Tweet not found'}, 404

class TweetList(Resource):
    args = {
        'tweets_ids': webargs.fields.DelimitedList(marshmallow.fields.Int(), missing=[]),
        'screen_name': marshmallow.fields.Str(missing=None),
        'user_id': marshmallow.fields.Int(missing=None),
        'url': marshmallow.fields.Str(missing=None),
        'cached_only': marshmallow.fields.Bool(missing=False),
        'from_date': marshmallow.fields.Date(missing=None)
    }

    @use_kwargs(args)
    def get(self, tweets_ids, screen_name, user_id, url, cached_only, from_date):
        print(tweets_ids, screen_name, user_id, url, cached_only, from_date)
        if tweets_ids:
            return entity_manager.get_tweets_from_ids(tweets_ids)
        elif user_id:
            return entity_manager.get_tweets_from_user_id(user_id, cached_only=cached_only, from_date=from_date)
        elif screen_name:
            return entity_manager.get_tweets_from_screen_name(screen_name, cached_only=cached_only, from_date=from_date)
        elif url:
            return entity_manager.get_tweets_containing_url(url, cached_only=cached_only, from_date=from_date)

        return {'error': 'Missing one of required params: tweet_ids, user_id, screen_name, url'}, 400

class TwitterAccount(Resource):
    def get(self, account_id):
        twitter_account = entity_manager.get_twitter_account_from_id(account_id)
        if twitter_account:
            return twitter_account
        return {'error': 'User not found'}, 404

class TwitterAccountList(Resource):
    args = {
        'followers_of': marshmallow.fields.Int(missing=None),
        'friends_of': marshmallow.fields.Int(missing=None),
        'screen_name': marshmallow.fields.Str(missing=None),
        'limit': marshmallow.fields.Int(missing=500),
        'offset': marshmallow.fields.Int(missing=0)
    }

    @use_kwargs(args)
    def get(self, followers_of, friends_of, screen_name, limit, offset):
        if followers_of:
            return entity_manager.get_twitter_account_followers_from_id(followers_of, limit, offset)
        elif friends_of:
            return entity_manager.get_twitter_account_friends_from_id(friends_of, limit, offset)
        elif screen_name:
            return entity_manager.get_twitter_account_from_screen_name(screen_name)

        return {'error': 'Missing one of required params: tweet_ids, user_id, screen_name, url'}, 400

class FactcheckingOrganisation(Resource):
    def get(self, org_id):
        organisation = entity_manager.get_factchecking_organisation_from_id(org_id)
        if organisation:
            return organisation
        return {'error': 'Factchecking organisation not found'}, 404

class FactcheckingOrganisationList(Resource):
    args = {
        'belongs_to_ifcn': marshmallow.fields.Bool(missing=None),
        'valid_ifcn': marshmallow.fields.Bool(missing=None),
        'country': marshmallow.fields.Str(missing=None)
    }

    @use_kwargs(args)
    def get(self, belongs_to_ifcn, valid_ifcn, country):
        return entity_manager.get_factchecking_organisations(belongs_to_ifcn=belongs_to_ifcn, valid_ifcn=valid_ifcn, country=country)