from flask_restplus import Resource, marshal_with, marshal
import marshmallow
import webargs
import flask_restplus
from webargs.flaskparser import use_args, use_kwargs

from ..model import analysis_manager


### types of output
count_analysis_fields = {
    'id': flask_restplus.fields.Integer(attribute='_id'),
    'screen_name': flask_restplus.fields.String,
    'profile_image_url': flask_restplus.fields.String,
    'tweets_cnt': flask_restplus.fields.Integer,
    'shared_urls_cnt': flask_restplus.fields.Integer,
    'verified_urls_cnt': flask_restplus.fields.Integer,
    'mixed_urls_cnt': flask_restplus.fields.Integer,
    'fake_urls_cnt': flask_restplus.fields.Integer,
    'unknown_urls_cnt': flask_restplus.fields.Integer,
    'score': flask_restplus.fields.Integer,
    'rebuttals': flask_restplus.fields.Raw,
    'fake_urls': flask_restplus.fields.Raw,
    'mixed_urls': flask_restplus.fields.Raw,
    'verified_urls': flask_restplus.fields.Raw,
    'updated': flask_restplus.fields.DateTime(dt_format='rfc822'),
    'cache': flask_restplus.fields.String
}

class UrlAnalysis(Resource):
    args = {
        'url': marshmallow.fields.Str(missing=None),
    }

    @use_kwargs(args)
    def get(self, url):
        """GET is for cached results"""
        print('request GET', url)
        if not url:
            return {'error': 'Provide an url as parameter'}, 400
        pass

    @use_kwargs(args)
    def post(self, url):
        """POST runs the analysis again"""
        print('request POST', url)
        if not url:
            return {'error': 'Provide an url as parameter'}, 400
        pass

class TweetAnalysis(Resource):
    args = {
        'tweet_id': marshmallow.fields.Int(missing=None),
    }

    @use_kwargs(args)
    def get(self, tweet_id):
        """GET is for cached results"""
        print('request GET', tweet_id)
        if not tweet_id:
            return {'error': 'Provide an tweet_id as parameter'}, 400
        pass

    @use_kwargs(args)
    def post(self, tweet_id):
        """POST runs the analysis again"""
        print('request POST', tweet_id)
        if not tweet_id:
            return {'error': 'Provide an tweet_id as parameter'}, 400
        pass

class TwitterAccountAnalysis(Resource):
    args = {
        'user_id': marshmallow.fields.Int(missing=None),
        'screen_name': marshmallow.fields.Str(missing=None),
        'relation': marshmallow.fields.String(missing=None),
        'limit': marshmallow.fields.Int(missing=500)
    }

    # TODO let it also be a path parameter
    @use_kwargs(args)
    @marshal_with(count_analysis_fields)
    def get(self, user_id, screen_name, relation, limit):
        """GET is for cached results"""
        allow_cached=True
        only_cached=True
        if relation == 'friends':
            return analysis_manager.analyse_friends_from_screen_name(screen_name, limit)
        if user_id:
            return analysis_manager.analyse_twitter_account(user_id, allow_cached=allow_cached, only_cached=only_cached)
        if screen_name:
            return analysis_manager.analyse_twitter_account_from_screen_name(screen_name, allow_cached=allow_cached, only_cached=only_cached)

        return {'error': 'Provide a user_id or screen_name as parameter'}, 400

    @use_kwargs(args)
    @marshal_with(count_analysis_fields)
    def post(self, user_id, screen_name, relation, limit):
        """POST runs the analysis again"""
        allow_cached=False
        only_cached=False
        if relation == 'friends':
            if user_id:
                return analysis_manager.analyse_friends(user_id, limit, allow_cached=allow_cached, only_cached=only_cached)
            if screen_name:
                return analysis_manager.analyse_friends_from_screen_name(screen_name, limit, allow_cached=allow_cached, only_cached=only_cached)
        if user_id:
            return analysis_manager.analyse_twitter_account(user_id, allow_cached=allow_cached, only_cached=only_cached)
        if screen_name:
            return analysis_manager.analyse_twitter_account_from_screen_name(screen_name, allow_cached=allow_cached, only_cached=only_cached)
        return {'error': 'Provide a user_id(s) or screen_name(s) as parameter'}, 400

class UrlTimeDistributionAnalysis(Resource):
    args = {
        'url': marshmallow.fields.Str(missing=None),
        'time_granularity': marshmallow.fields.Str(missing='month', validate=lambda tg: tg in ['year', 'month', 'week', 'day'])
    }

    @use_kwargs(args)
    def get(self, url, time_granularity):
        if not url:
            return {'error': 'missing parameter url'}, 400
        return analysis_manager.analyse_time_distribution_url(url, time_granularity)

class TweetsTimeDistributionAnalysis(Resource):
    args = {
        'tweets_ids': webargs.fields.DelimitedList(marshmallow.fields.Int(), missing=[]),
        'time_granularity': marshmallow.fields.Str(missing='month', validate=lambda tg: tg in ['year', 'month', 'week', 'day']),
        'mode': marshmallow.fields.Str(missing='absolute', validate=lambda m: m in ['absolute', 'relative']),
        'reference_date': marshmallow.fields.Date(missing=None)
    }

    @use_kwargs(args)
    def get(self, tweets_ids, time_granularity, mode, reference_date):
        return analysis_manager.analyse_time_distribution_tweets(tweets_ids, time_granularity, mode, reference_date)
