from flask_restful import Resource
import marshmallow
import webargs
from webargs.flaskparser import use_args, use_kwargs

from ..model import analysis_manager


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
        'user_ids': webargs.fields.DelimitedList(marshmallow.fields.Int(), missing=[]),
        'screen_name': marshmallow.fields.Str(missing=None),
        'screen_names': webargs.fields.DelimitedList(marshmallow.fields.Str(), missing=[]),
        'allow_cached': marshmallow.fields.Bool(missing=True),
        'only_cached': marshmallow.fields.Bool(missing=False)
    }

    # TODO let it also be a path parameter
    @use_kwargs(args)
    def get(self, user_id, user_ids, screen_name, screen_names, allow_cached, only_cached):
        """GET is for cached results"""
        return self.post(user_id=user_id, user_ids=user_ids, screen_name=screen_name, screen_names=screen_names, allow_cached=True, only_cached=True)

    @use_kwargs(args)
    def post(self, user_id, user_ids, screen_name, screen_names, allow_cached, only_cached):
        """POST runs the analysis again"""
        if user_id:
            return analysis_manager.analyse_twitter_account(user_id, allow_cached=allow_cached, only_cached=only_cached)
        elif user_ids:
            return analysis_manager.analyse_twitter_accounts(user_ids, allow_cached=allow_cached, only_cached=only_cached)
        elif screen_name:
            return analysis_manager.analyse_twitter_account_from_screen_name(screen_name, allow_cached=allow_cached, only_cached=only_cached)
        elif screen_names:
            return analysis_manager.analyse_twitter_accounts_from_screen_name(screen_names, allow_cached=allow_cached, only_cached=only_cached)
        return {'error': 'Provide a user_id(s) or screen_name(s) as parameter'}, 400

class TimeAnalysisDistribution(Resource):
    args = {
        'url': marshmallow.fields.Str(missing=None)
    }