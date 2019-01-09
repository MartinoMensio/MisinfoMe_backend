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

app = Flask(__name__)
CORS(app)
ma = Marshmallow(app)
#api = Api(app)

mappings = {}
mappings_path = 'cache/url_mappings.json'
if os.path.isfile(mappings_path):
     with open(mappings_path) as f:
          mappings = json.load(f)

info = data.load_data()
bearer_token = twitter.get_bearer_token()

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
    res = data.classify_url(url, info)
    return jsonify({'result': res})

@app.route('/tweets')
def get_tweets_from_display_name():
    handle = request.args.get('handle')
    tweets = twitter.get_user_tweets(bearer_token, handle)
    return jsonify(tweets)

@app.route('/tweets_api')
def get_tweets_from_display_name2():
    handle = request.args.get('handle')
    tweets = twitter.get_user_tweets_api(bearer_token, handle)
    return jsonify(tweets)

@app.route('/followers_api')
def get_followers():
    handle = request.args.get('handle')
    followers = twitter.get_followers_api(bearer_token, handle)
    return jsonify(followers)

@app.route('/following_api')
def get_following():
    handle = request.args.get('handle')
    following = twitter.get_followers_api(bearer_token, handle)
    return jsonify(following)

@app.route('/urls')
def get_shared_urls():
    handle = request.args.get('handle')
    tweets = twitter.get_user_tweets(bearer_token, handle)
    urls = twitter.get_urls_from_tweets(tweets, mappings)
    return jsonify(urls)

@app.route('/urls_api')
def get_shared_urls_api():
    handle = request.args.get('handle')
    tweets = twitter.get_user_tweets_api(bearer_token, handle)
    urls = twitter.get_urls_from_tweets(tweets, mappings)
    return jsonify(urls)

@app.route('/evaluate_old')
@cross_origin()
def evaluate_user():
    handle = request.args.get('handle')
    tweets = twitter.get_user_tweets(bearer_token, handle)
    urls = twitter.get_urls_from_tweets(tweets, mappings)
    result = evaluate.count(urls, info, tweets, handle)
    return jsonify(result)

def get_tweets_wrap(handle):
    return twitter.get_user_tweets_api(bearer_token, handle)

@app.route('/analyse/tweets')
@cross_origin()
def analyse_tweets():
    """from a list of tweet IDs (comma-separated) retrieves and analyses them"""
    tweet_ids = request.args.get('ids')
    tweets = twitter.get_statuses_lookup(bearer_token, tweet_ids)
    urls = twitter.get_urls_from_tweets(tweets, mappings)
    result = evaluate.count(urls, info, tweets, None)
    return jsonify(result)

@app.route('/analyse/user')
@cross_origin()
def analyse_user():
    handle = request.args.get('handle')
    tweets = twitter.get_user_tweets_api(bearer_token, handle)
    urls = twitter.get_urls_from_tweets(tweets, mappings)
    result = evaluate.count(urls, info, tweets, handle)
    # evaluate also the following
    include_following = request.args.get('include_following')
    print(include_following)
    if include_following:
        result['following'] = {}
        following = twitter.get_followers_api(bearer_token, handle)
        print(len(following), 'following')
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for f, tweets_f in zip(following, executor.map(get_tweets_wrap, following)):
                urls_f = twitter.get_urls_from_tweets(tweets_f, mappings)
                result_f = evaluate.count(urls_f, info, tweets_f, handle)
                result['following'][f] = result_f['you']
        """for f in following:
            tweets_f = twitter.get_user_tweets_api(bearer_token, f)
            urls_f = twitter.get_urls_from_tweets(tweets_f, mappings)
            result_f = evaluate.count(urls_f, info, tweets_f, handle)
            result['following'][f] = result_f['you']"""
    return jsonify(result)

@app.route('/mappings')
def get_mappings():
     return jsonify(mappings)

if __name__ == '__main__':
     app.run()