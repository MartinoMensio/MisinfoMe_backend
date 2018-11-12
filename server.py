from flask import Flask, request, jsonify
#from flask_restful import Resource, Api
from json import dumps
from dotenv import load_dotenv, find_dotenv
from flask_cors import CORS, cross_origin


load_dotenv()

import data
import twitter
import evaluate

app = Flask(__name__)
CORS(app)
#api = Api(app)

tagged_url = data.load_data(by_url=True)
bearer_token = twitter.get_bearer_token()

@app.route('/classify')
def get_class_for_url():
    url = request.args.get('url')
    res = tagged_url.get(url, None)
    return jsonify({'result': res})

@app.route('/tweets')
def get_tweets_from_display_name():
    handle = request.args.get('handle')
    tweets = twitter.get_user_tweets(bearer_token, handle)
    return jsonify(tweets)

@app.route('/tweets_old')
def get_tweets_from_display_name2():
    handle = request.args.get('handle')
    tweets = twitter.get_user_tweets_old(bearer_token, handle)
    return jsonify(tweets)

@app.route('/urls')
def get_shared_urls():
    handle = request.args.get('handle')
    tweets = twitter.get_user_tweets(bearer_token, handle)
    urls = twitter.get_urls_from_tweets(tweets)
    return jsonify(urls)

@app.route('/urls_old')
def get_shared_urls_old():
    handle = request.args.get('handle')
    tweets = twitter.get_user_tweets_old(bearer_token, handle)
    urls = twitter.get_urls_from_tweets(tweets)
    return jsonify(urls)

@app.route('/evaluate')
@cross_origin()
def evaluate_user():
    handle = request.args.get('handle')
    tweets = twitter.get_user_tweets(bearer_token, handle)
    urls = twitter.get_urls_from_tweets(tweets)
    result = evaluate.count(urls, tagged_url, tweets)
    return jsonify(result)

@app.route('/evaluate_old')
@cross_origin()
def evaluate_user_old():
    handle = request.args.get('handle')
    tweets = twitter.get_user_tweets_old(bearer_token, handle)
    urls = twitter.get_urls_from_tweets(tweets)
    result = evaluate.count(urls, tagged_url, tweets)
    return jsonify(result)


if __name__ == '__main__':
     app.run()