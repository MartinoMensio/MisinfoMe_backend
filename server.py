import os
import json

import concurrent.futures

from flask import Flask, request, jsonify
#from flask_restful import Resource, Api
from json import dumps
from dotenv import load_dotenv, find_dotenv
from flask_cors import CORS, cross_origin
from flask_marshmallow import Marshmallow


load_dotenv()

import data
import twitter
import evaluate
import url_redirect_manager

app = Flask(__name__)
CORS(app)
ma = Marshmallow(app)
#api = Api(app)

twitterApi = twitter.TwitterAPI()

'''
# Marshmallow schemas
class AnalysisSchema(ma.schema):
     class Meta:
          # fields to expose
          fields = ()
'''


@app.route('/analyse/url')
def analyse_url():
    url = request.args.get('url')
    res = data.classify_url({'resolved': url, 'found_in_tweet': 0, 'retweet': False})
    return jsonify({'result': res})

@app.route('/tweets')
def get_tweets_from_display_name2():
    handle = request.args.get('handle')
    tweets = twitterApi.get_user_tweets(handle)
    return jsonify(tweets)

@app.route('/followers')
def get_followers():
    handle = request.args.get('handle')
    followers = twitterApi.get_followers(handle)
    return jsonify(followers)

@app.route('/following')
def get_following():
    handle = request.args.get('handle')
    following = twitterApi.get_following(handle)
    return jsonify(following)

@app.route('/urls')
def get_shared_urls():
    handle = request.args.get('handle')
    tweets = twitterApi.get_user_tweets(handle)
    urls = twitter.get_urls_from_tweets(tweets)
    return jsonify(urls)

def get_tweets_wrap(handle):
    return twitterApi.get_user_tweets(handle)

@app.route('/analyse/tweets')
@cross_origin()
def analyse_tweets():
    """from a list of tweet IDs (comma-separated) retrieves and analyses them"""
    tweet_ids_param = request.args.get('ids')
    tweet_ids = []
    if tweet_ids_param:
        tweet_ids = tweet_ids_param.split(',')
    tweets = twitterApi.get_statuses_lookup(tweet_ids)
    urls = twitter.get_urls_from_tweets(tweets)
    result = evaluate.count(urls, tweets, None)
    return jsonify(result)

@app.route('/analyse/user')
@cross_origin()
def analyse_user():
    handle = request.args.get('handle')
    tweets = twitterApi.get_user_tweets(handle)
    urls = twitter.get_urls_from_tweets(tweets)
    result = evaluate.count(urls, tweets, handle)
    # evaluate also the following
    include_following = request.args.get('include_following')
    print(include_following)
    if include_following:
        result['following'] = {}
        following = twitterApi.get_following(handle)
        print(len(following), 'following')
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for f, tweets_f in zip(following, executor.map(get_tweets_wrap, following)):
                urls_f = twitter.get_urls_from_tweets(tweets_f)
                result_f = evaluate.count(urls_f, tweets_f, handle)
                result['following'][f] = result_f['you']
    return jsonify(result)

@app.route('/analyse/user/network')
@cross_origin()
def analyse_user_network():
    handle = request.args.get('handle')
    # evaluate the following
    following_analysis = {}
    following = twitterApi.get_following(handle)
    print(len(following), 'following')
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for f, tweets_f in zip(following, executor.map(get_tweets_wrap, following)):
            urls_f = twitter.get_urls_from_tweets(tweets_f)
            result_f = evaluate.count(urls_f, tweets_f, handle)
            following_analysis[f] = result_f['you']
    result = {
        'fake_urls_cnt': sum([el['fake_urls_cnt'] for el in following_analysis.values()]),
        'shared_urls_cnt': sum([el['shared_urls_cnt'] for el in following_analysis.values()]),
        'verified_urls_cnt': sum([el['verified_urls_cnt'] for el in following_analysis.values()]),
        'tweets_cnt': sum([el['tweets_cnt'] for el in following_analysis.values()]),
        'unknown_urls_cnt': sum([el['unknown_urls_cnt'] for el in following_analysis.values()])
    }
    return jsonify(result)

@app.route('/mappings')
def get_redirect_for():
    url = request.args.get('url')
    url_redirect_manager.get_redirect_for(url)
    return jsonify(mappings)

if __name__ == '__main__':
    app.run()