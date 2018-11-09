from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from json import dumps
from dotenv import load_dotenv, find_dotenv
load_dotenv()

import data
import twitter
import evaluate

app = Flask(__name__)
api = Api(app)

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

@app.route('/urls')
def get_shared_urls():
    handle = request.args.get('handle')
    tweets = twitter.get_user_tweets(bearer_token, handle)
    urls = twitter.get_urls_from_tweets(tweets)
    return jsonify(urls)

@app.route('/evaluate')
def evaluate_user():
    handle = request.args.get('handle')
    tweets = twitter.get_user_tweets(bearer_token, handle)
    urls = twitter.get_urls_from_tweets(tweets)
    result = evaluate.count(urls, tagged_url)
    return jsonify(result)


if __name__ == '__main__':
     app.run(port='5000')