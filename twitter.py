import requests
import os
import base64
#from lxml import etree
from bs4 import BeautifulSoup

from twitterscraper.query import query_tweets_from_user

from requests.auth import HTTPBasicAuth

#htmlparser = etree.HTMLParser()

def get_bearer_token():
    # these env variables must be there
    tw_key = os.environ['TWITTER_API_KEY']
    tw_secret = os.environ['TWITTER_API_SECRET']
    response = requests.post('https://api.twitter.com/oauth2/token', data={'grant_type': 'client_credentials'}, auth=HTTPBasicAuth(tw_key, tw_secret)).json()
    assert response['token_type'] == 'bearer'
    print('twitter OK')
    return response['access_token']

def get_user_tweets_old(bearer_token, user_handle):
    headers = {'Authorization': 'Bearer {}'.format(bearer_token)}#.format(base64.b64encode(bearer_token.encode('utf-8')))}
    params = {'screen_name': user_handle, 'max_count': 200}
    all_tweets = []
    while True:
        response = requests.get('https://api.twitter.com/1.1/statuses/user_timeline.json', headers=headers, params=params).json()
        if 'errors' in response:
            print(response)
            raise ValueError()

        print('.', end='', flush=True)
        all_tweets.extend(response)
        if not len(response):
            break
        # set the maximum id allowed from the last tweet, and -1 to avoid duplicates
        max_id = response[-1]['id'] - 1
        params['max_id'] = max_id
    print('retrieved', len(all_tweets), 'tweets')
    return all_tweets

def get_user_tweets(bearer_token, user_handle):
    list_of_tweets = query_tweets_from_user(user_handle)
    results = [{'entities': {'urls': get_urls_scraper(t)}} for t in list_of_tweets]
    return results

def get_urls_scraper(tweet):
    # get from html with BeautifulSoup
    soup = BeautifulSoup(tweet.html, 'html.parser')
    #tree = etree.parse(tweet['html'], htmlparser)
    urls = [{'expanded_url': el['data-expanded-url']} for el in soup.select('a[data-expanded-url]')]
    return urls


def get_urls_from_tweets(tweets):
    all_urls = []
    for t in tweets:
        urls = t['entities']['urls']
        all_urls.extend(urls)

    source_urls = [el['expanded_url'] for el in all_urls]

    return source_urls
