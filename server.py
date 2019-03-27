import os
import json

import concurrent.futures

from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
#from flask_restful import Resource, Api
from json import dumps
from dotenv import load_dotenv, find_dotenv
from flask_cors import CORS, cross_origin
from flask_marshmallow import Marshmallow
import json


load_dotenv()

import data
import database
import twitter
import evaluate
import model
import unshortener


app = Flask(__name__)
CORS(app)
ma = Marshmallow(app)
#api = Api(app)

twitter_api = twitter.TwitterAPI()

BASE_URL = os.environ.get('BASE_URL', '/misinfo')
print('BASE_URL', BASE_URL)
API_URL = BASE_URL + '/api'
APP_URL = BASE_URL + '/app'


class MyEncoder(json.JSONEncoder):
    def default(self, o): # pylint: disable=method-hidden
        return o.__dict__




### Endpoints with tree explaination for the score

@app.route(API_URL + '/analyse_tree/domain')
def analyse_domain():
    domain = request.args.get('domain')
    print(domain)
    result = evaluate.evaluate_domain(domain)
    #return jsonify(result.to_dict())
    return jsonify(json.loads(MyEncoder().encode(result)))

@app.route(API_URL + '/analyse_tree/url')
def analyse_url():
    url = request.args.get('url')
    print(url)
    result = evaluate.evaluate_url(url)
    #return jsonify(result.to_dict())
    return jsonify(json.loads(MyEncoder().encode(result)))

@app.route(API_URL + '/analyse_tree/tweets/<tweet_id>')
def analyse_tweet(tweet_id):
    result = evaluate.evaluate_tweet(tweet_id, twitter_api)
    return jsonify(json.loads(MyEncoder().encode(result)))

@app.route(API_URL + '/analyse_tree/users/<user_id>')
def analyse_twitter_user(user_id):
    user_id = int(user_id)
    result = evaluate.evaluate_twitter_user(user_id, twitter_api)
    return jsonify(json.loads(MyEncoder().encode(result)))

@app.route(API_URL + '/analyse_tree/users')
def analyse_twitter_user_from_screen_name():
    screen_name = request.args.get('screen_name')
    print(screen_name)
    result = evaluate.evaluate_twitter_user_from_screen_name(screen_name, twitter_api)
    return jsonify(json.loads(MyEncoder().encode(result)))




@app.route(API_URL + '/about')
@cross_origin()
def get_about():
    return jsonify(database.get_collections_stats())

@app.route(API_URL + '/about/datasets')
@cross_origin()
def get_datasets():
    return jsonify([el for el in database.get_datasets()])

@app.route(API_URL + '/about/domains')
@cross_origin()
def get_domains():
    return jsonify([el for el in database.get_domains()])

@app.route(API_URL + '/about/domains_vs_datasets_table')
def get_domains_vs_datasets():
    return jsonify(data.get_domains_vs_datasets_table())

@app.route(API_URL + '/about/fact_checkers')
def get_fact_checkers():
    return jsonify(data.get_fact_checkers())

@app.route(API_URL + '/about/fact_checkers_table')
def get_fact_checkers_table():
    return jsonify(data.get_fact_checkers_table())







####################################################
# Endpoints for the entities

@app.route(API_URL + '/entities/tweets')
def get_tweets_from_screen_name():
    screen_name = request.args.get('screen_name')
    tweets = twitter_api.get_user_tweets_from_screen_name(screen_name)
    return jsonify(tweets)

@app.route(API_URL + '/followers')
def get_followers():
    screen_name = request.args.get('screen_name')
    limit = request.args.get('limit', None)
    if limit:
        limit = int(limit)
    followers = twitter_api.get_followers(screen_name, limit)
    return jsonify(followers)

@app.route(API_URL + '/following')
def get_following():
    screen_name = request.args.get('screen_name')
    limit = request.args.get('limit', None)
    if limit:
        limit = int(limit)
    following = twitter_api.get_following(screen_name, limit)
    return jsonify(following)

@app.route(API_URL + '/urls')
def get_shared_urls():
    screen_name = request.args.get('screen_name')
    tweets = twitter_api.get_user_tweets_from_screen_name(screen_name)
    urls = twitter.get_urls_from_tweets(tweets)
    return jsonify(urls)


### Counting URLs API

@app.route(API_URL + '/count_urls/users', methods = ['GET', 'POST'])
@cross_origin()
def count_user():
    # allow_cached is useful when I would just like a result, so it does not update it if the analysis has been run already
    allow_cached = request.args.get('allow_cached', False)
    # only get already evaluated profiles
    only_cached = request.args.get('only_cached', False)
    #print(request.is_json)
    if request.is_json:
        # retrieve content from json POST content
        content = request.get_json()
        screen_names_splitted = content.get('screen_names', [])
        allow_cached = content.get('allow_cached', allow_cached)
        only_cached = content.get('only_cached', only_cached)
    else:
        screen_names = request.args.get('screen_names')

        screen_names_splitted = screen_names.split(',')

    if len(screen_names_splitted) == 1:
        result = evaluate.count_user_from_screen_name(screen_names_splitted[0], twitter_api, allow_cached, only_cached)
    else:
        result = evaluate.count_users(screen_names_splitted, twitter_api, allow_cached, only_cached)

    return jsonify(result)

@app.route(API_URL + '/count_urls/users/<user_id>')
def count_user_from_id(user_id):
    user_id = int(user_id)
    result = evaluate.count_user(user_id, twitter_api, True, False)
    return jsonify(result)

@app.route(API_URL + '/count_urls/overall')
@cross_origin()
def get_overall_counts():
    return jsonify(evaluate.get_overall_counts())

@app.route(API_URL + '/users_stored')
def get_users_stored():
    return jsonify([el['_id'] for el in database.get_users_id()])


@app.route(API_URL + '/factchecking_by_domain')
def get_factchecking_by_domain():
    domain = request.args.get('from')
    if domain:
        result = evaluate.get_factchecking_by_one_domain(domain, twitter_api)
    else:
        result = evaluate.get_factchecking_by_domain()
    return jsonify(result)

@app.route(API_URL + '/factchecking_by_factchecker')
def get_factchecking_by_factchecker():
    result = evaluate.get_factchecking_by_factchecker()
    return jsonify(result)

@app.route(API_URL + '/tweets_from_url')
def get_tweets_containing_url():
    url = request.args.get('url')
    if not url:
        raise ValueError('no url')
    result = data.get_tweets_containing_url(url, twitter_api)
    return jsonify(result)



@app.route(API_URL + '/tweets_time_distrib', methods = ['POST'])
def get_tweets_time_distrib():
    if request.is_json:
        # retrieve content from json POST content
        content = request.get_json()
        tweet_ids = content.get('tweet_ids', [])
        time_granularity = content.get('time_granularity', 'month')
        mode = content.get('mode', 'absolute') # absolute means just time, relative is relative to reference_time (argument)
        reference_time = content.get('reference_time', None)
        result = evaluate.analyse_tweet_time(tweet_ids, time_granularity, mode, reference_time, twitter_api)
    else:
        return jsonify({'error': 'not JSON request'})
    return jsonify(result)

@app.route(API_URL + '/url_time_distrib')
def get_time_distrib():
    url = request.args.get('url')
    time_granularity = request.args.get('time_granularity', 'month')
    result = evaluate.analyse_url_distribution(url, twitter_api, time_granularity=time_granularity)
    return jsonify(result)

@app.route(API_URL + '/url_time_published')
def get_url_published_time():
    url = request.args.get('url')
    result = evaluate.get_url_publish_date(url)
    return jsonify(result)


# Other useful APIs

@app.route(API_URL + '/resolve_url')
def get_redirect_for():
    url = request.args.get('url')
    unshortened = unshortener.unshorten(url)
    return jsonify(unshortened)

@app.route(BASE_URL + '/static/<path:path>')
def static_proxy(path):
    # the static files
    #print(path)
    return send_from_directory('app', path)


@app.route(BASE_URL + '/app/<path:path>')
@app.route(BASE_URL + '/app/')
def deep_linking(path=None):
    # send the angular application, mantaining the state informations (no redirects)
    return send_from_directory('app', 'index.html')

@app.route('/')
@app.route(BASE_URL)
@app.route(BASE_URL + '/')
@app.route(BASE_URL + '/app')
def redirect_home():
    # this route is for sending the user to the homepage
    return redirect(BASE_URL + '/app/home')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)