# DEPRECATED: this module contains the API that still need to be migrated
import os
import json

import concurrent.futures

from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_restplus import Resource, Api
from json import dumps
from dotenv import load_dotenv, find_dotenv
from flask_cors import CORS, cross_origin
from flask_marshmallow import Marshmallow
import json


load_dotenv()

from api.data import data
from api.data import database
from api.data import twitter
from api.evaluation import evaluate
from api.evaluation import model
from api.data import unshortener


app = Flask(__name__)
CORS(app)
ma = Marshmallow(app)
api = Api(app)


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




@app.route(API_URL + '/about/domains_vs_datasets_table')
def get_domains_vs_datasets():
    return jsonify(data.get_domains_vs_datasets_table())

@app.route(API_URL + '/about/fact_checkers')
def get_fact_checkers():
    return jsonify(data.get_fact_checkers())






####################################################
# Endpoints for the entities

@app.route(API_URL + '/urls')
def get_shared_urls():
    screen_name = request.args.get('screen_name')
    tweets = twitter_api.get_user_tweets_from_screen_name(screen_name)
    urls = twitter.get_urls_from_tweets(tweets)
    return jsonify(urls)


@app.route(API_URL + '/count_urls/users/<user_id>')
def count_user_from_id(user_id):
    user_id = int(user_id)
    result = evaluate.count_user(user_id, twitter_api, True, False)
    return jsonify(result)

@app.route(API_URL + '/users_stored')
def get_users_stored():
    return jsonify([el['_id'] for el in database.get_users_id()])


# TODO:refactor
@app.route(API_URL + '/factchecking_by_domain')
def get_factchecking_by_domain():
    domain = request.args.get('from')
    if domain:
        result = evaluate.get_factchecking_by_one_domain(domain, twitter_api)
    else:
        result = evaluate.get_factchecking_by_domain()
    return jsonify(result)
