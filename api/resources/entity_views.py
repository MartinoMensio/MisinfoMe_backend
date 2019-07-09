from flask_restplus import Resource, marshal_with
import flask_restplus
import webargs
import marshmallow
from webargs.flaskparser import use_args, use_kwargs

from ..model import entity_manager
from . import statuses

tweet_object = {
    'id': flask_restplus.fields.Integer,
    'text': flask_restplus.fields.String(attribute='full_text'),
    'error': flask_restplus.fields.String
}

twitter_account_object = {
    'id': flask_restplus.fields.Integer,
    'name': flask_restplus.fields.String,
    'screen_name': flask_restplus.fields.String,
    'profile_image_url_https': flask_restplus.fields.String,
    'error': flask_restplus.fields.String
}


class Tweet(Resource):
    @marshal_with(tweet_object)
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

    @marshal_with(tweet_object)
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
    @marshal_with(twitter_account_object)
    def get(self, account_id):
        twitter_account = entity_manager.get_twitter_account_from_id(account_id)
        if twitter_account:
            return twitter_account
        return {'error': 'User not found'}, 404

class TwitterAccountList(Resource):
    args = {
        'relation': marshmallow.fields.Str(missing=None, validate=lambda r: r in ['followers', 'friends']),
        'screen_name': marshmallow.fields.Str(missing=None),
        'account_id': marshmallow.fields.Int(missing=None),
        'limit': marshmallow.fields.Int(missing=500),
        'offset': marshmallow.fields.Int(missing=0),
        'cached': marshmallow.fields.Int(missing=False)
    }

    @marshal_with(twitter_account_object)
    @use_kwargs(args)
    def get(self, relation, screen_name, account_id, limit, offset, cached):
        if relation == 'followers':
            if account_id:
                return entity_manager.get_twitter_account_followers_from_id(account_id, limit, offset)
            elif screen_name:
                return entity_manager.get_twitter_account_followers_from_screen_name(screen_name, limit, offset)
            else:
                return {'error': 'followers of?'}
        elif relation == 'friends':
            if account_id:
                return entity_manager.get_twitter_account_friends_from_id(account_id, limit, offset)
            elif screen_name:
                return entity_manager.get_twitter_account_friends_from_screen_name(screen_name, limit, offset)
            else:
                return {'error': 'friends of?'}
        # no relationship
        elif screen_name:
            result = entity_manager.get_twitter_account_from_screen_name(screen_name, cached)
            if 'errors' in result:
                return {'error': result['errors'][0]['message']}
            return result
        elif account_id:
            result = entity_manager.get_twitter_account_from_id(account_id, cached)
            if 'errors' in result:
                return {'error': result['errors'][0]['message']}
            return result

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

# Fact-checking reviews

class FactcheckingReviewList(Resource):
    args = {
        'published_by_id': marshmallow.fields.String(missing=None),
        'published_at_domain': marshmallow.fields.String(missing=None),
        'published_at_url': marshmallow.fields.String(missing=None)
    }

    @use_kwargs(args)
    def get(self, published_by_id, published_at_domain, published_at_url):
        if published_by_id:
            return entity_manager.get_factchecking_reviews_from_organisation_id(published_by_id)
        elif published_at_domain:
            return entity_manager.get_factchecking_reviews_at_domain(published_at_domain)
        elif published_at_url:
            return entity_manager.get_factchecking_reviews_at_url(published_at_url)
        else:
            return entity_manager.get_factchecking_reviews_by_factchecker()



class DataStats(Resource):
    def get(self):
        return entity_manager.get_data_stats()

class DomainsStats(Resource):
    def get(self):
        return entity_manager.get_domains()

class SourcesStats(Resource):
    def get(self):
        return entity_manager.get_sources()

class FactcheckersTable(Resource):
    def get(self):
        return entity_manager.get_factcheckers_table()
