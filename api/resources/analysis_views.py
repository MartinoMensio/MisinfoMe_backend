from flask_restplus import Resource, marshal_with, marshal, Namespace
import marshmallow
import webargs
import flask_restplus
from webargs.flaskparser import use_args, use_kwargs

from ..model import analysis_manager, jobs_manager

api = Namespace('analysis', description='Analysis of some entities')

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

@api.route('/urls')
class UrlAnalysis(Resource):
    args = {
        'url': marshmallow.fields.Str(missing=None),
    }

    @api.param('url', 'The URL to be analysed')
    @use_kwargs(args)
    def get(self, url):
        """GET is for cached results"""
        print('request GET', url)
        if not url:
            return {'error': 'Provide an url as parameter'}, 400
        pass


    @api.param('url', 'The URL to be analysed')
    @use_kwargs(args)
    def post(self, url):
        """POST runs the analysis again"""
        print('request POST', url)
        if not url:
            return {'error': 'Provide an url as parameter'}, 400
        pass

@api.route('/tweets')
class TweetAnalysis(Resource):
    args = {
        'tweet_id': marshmallow.fields.Int(missing=None),
    }

    @api.param('tweet_id', 'The ID of the tweet to analyse')
    @use_kwargs(args)
    def get(self, tweet_id):
        """GET is for cached results"""
        print('request GET', tweet_id)
        if not tweet_id:
            return {'error': 'Provide an tweet_id as parameter'}, 400
        pass


    @api.param('tweet_id', 'The ID of the tweet to analyse')
    @use_kwargs(args)
    def post(self, tweet_id):
        """POST runs the analysis again"""
        print('request POST', tweet_id)
        if not tweet_id:
            return {'error': 'Provide an tweet_id as parameter'}, 400
        pass

@api.route('/twitter_accounts')
class TwitterAccountAnalysis(Resource):
    args = {
        'user_id': marshmallow.fields.Int(missing=None),
        'screen_name': marshmallow.fields.Str(missing=None),
        'relation': marshmallow.fields.String(missing=None),
        'limit': marshmallow.fields.Int(missing=500),
        'use_credibility': marshmallow.fields.Boolean(missing=False),
        'wait': marshmallow.fields.Boolean(missing=True)
    }

    @api.param('user_id', 'The user ID to analyse')
    @api.param('screen_name', 'The screen_name to analyse')
    @api.param('relation', 'if set to `friends` will analyse the friends instead of the user itself')
    @api.param('limit', 'if `relation` is set to `friends`, this tells how many friends maximum to analyse')
    @api.param('use_credibility', 'Wether to use the old model (false) or the new one based on credibility (legacy data interface as the old model)')
    @api.param('wait', description='Do you want to be waiting, or get a work id that you can query later?', type=bool, missing=True)
    @use_kwargs(args)
    # @marshal_with(count_analysis_fields)
    def get(self, user_id, screen_name, relation, limit, use_credibility, wait):
        """GET is for cached results"""
        allow_cached=True
        only_cached=True
        if wait:
            if relation == 'friends':
                result = analysis_manager.analyse_friends_from_screen_name(screen_name, limit, use_credibility=use_credibility)
            elif user_id:
                result = analysis_manager.analyse_twitter_account(user_id, allow_cached=allow_cached, only_cached=only_cached, use_credibility=use_credibility)
            elif screen_name:
                result = analysis_manager.analyse_twitter_account_from_screen_name(screen_name, allow_cached=allow_cached, only_cached=only_cached, use_credibility=use_credibility)
            return marshal(result, count_analysis_fields), 200
        else:
            if relation == 'friends':
                return {'error': 'async job not supported with this combination of parameters. set wait=False'}, 400
            elif user_id:
                return {'error': 'async job not supported with this combination of parameters. set wait=False'}, 400
            elif screen_name:
                return jobs_manager.create_task_for(analysis_manager.analyse_twitter_account_from_screen_name, screen_name, allow_cached=allow_cached, only_cached=only_cached, use_credibility=use_credibility)

        return {'error': 'Provide a user_id or screen_name as parameter'}, 400

    @api.param('user_id', 'The user ID to analyse')
    @api.param('screen_name', 'The screen_name to analyse')
    @api.param('relation', 'if set to `friends` will analyse the friends instead of the user itself')
    @api.param('limit', 'if `relation` is set to `friends`, this tells how many friends maximum to analyse')
    @api.param('use_credibility', 'Wether to use the old model (false) or the new one based on credibility')
    @api.param('wait', description='Do you want to be waiting, or get a work id that you can query later?', type=bool, missing=True)
    @use_kwargs(args)
    #@marshal_with(count_analysis_fields)
    def post(self, user_id, screen_name, relation, limit, use_credibility, wait):
        """POST runs the analysis again"""
        allow_cached=False
        only_cached=False
        if wait:
            if relation == 'friends':
                if user_id:
                    result = analysis_manager.analyse_friends(user_id, limit, allow_cached=allow_cached, only_cached=only_cached, use_credibility=use_credibility)
                elif screen_name:
                    result = analysis_manager.analyse_friends_from_screen_name(screen_name, limit, allow_cached=allow_cached, only_cached=only_cached, use_credibility=use_credibility)
            elif user_id:
                result = analysis_manager.analyse_twitter_account(user_id, allow_cached=allow_cached, only_cached=only_cached, use_credibility=use_credibility)
            elif screen_name:
                result = analysis_manager.analyse_twitter_account_from_screen_name(screen_name, allow_cached=allow_cached, only_cached=only_cached, use_credibility=use_credibility)
            return marshal(result, count_analysis_fields), 200
        else:
            if relation == 'friends':
                return {'error': 'async job not supported with this combination of parameters. set wait=False'}, 400
            elif user_id:
                return {'error': 'async job not supported with this combination of parameters. set wait=False'}, 400
            elif screen_name:
                return jobs_manager.create_task_for(analysis_manager.analyse_twitter_account_from_screen_name, screen_name, allow_cached=allow_cached, only_cached=only_cached, use_credibility=use_credibility)
        return {'error': 'Provide a user_id(s) or screen_name(s) as parameter'}, 400

@api.route('/time_distribution_url')
class UrlTimeDistributionAnalysis(Resource):
    args = {
        'url': marshmallow.fields.Str(missing=None),
        'time_granularity': marshmallow.fields.Str(missing='month', validate=lambda tg: tg in ['year', 'month', 'week', 'day'])
    }

    @api.param('url', 'The url to analyse temporally')
    @api.param('time_granularity', 'The time granularity wanted. Possible values are `year`, `month`, `week`, `day`')
    @use_kwargs(args)
    def get(self, url, time_granularity):
        if not url:
            return {'error': 'missing parameter url'}, 400
        return analysis_manager.analyse_time_distribution_url(url, time_granularity)

@api.route('/time_distribution_tweets')
class TweetsTimeDistributionAnalysis(Resource):
    args = {
        'tweets_ids': webargs.fields.DelimitedList(marshmallow.fields.Int(), missing=[]),
        'time_granularity': marshmallow.fields.Str(missing='month', validate=lambda tg: tg in ['year', 'month', 'week', 'day']),
        'mode': marshmallow.fields.Str(missing='absolute', validate=lambda m: m in ['absolute', 'relative']),
        'reference_date': marshmallow.fields.Date(missing=None)
    }

    @api.param('tweets_ids', 'The IDs of the tweets to analyse')
    @api.param('time_granularity', 'The time granularity wanted. Possible values are `year`, `month`, `week`, `day`')
    @api.param('mode', 'The mode for time. Possible values are `absolute`, `relative`')
    @use_kwargs(args)
    def get(self, tweets_ids, time_granularity, mode, reference_date):
        return analysis_manager.analyse_time_distribution_tweets(tweets_ids, time_granularity, mode, reference_date)
