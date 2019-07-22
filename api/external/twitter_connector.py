import os
import requests

from . import ExternalException

TWITTER_CONNECTOR = os.environ.get('TWITTER_CONNECTOR', 'http://localhost:20200/')
print('TWITTER_CONNECTOR', TWITTER_CONNECTOR)

def get_twitter_user(user_id):
    response = requests.get(f'{TWITTER_CONNECTOR}users/{user_id}')
    if response.status_code != 200:
        raise ValueError(response.status_code)
    return response.json()

def get_user_tweets(user_id):
    response = requests.get(f'{TWITTER_CONNECTOR}users/{user_id}/tweets')
    if response.status_code != 200:
        raise ValueError(response.status_code)
    return response.json()

def search_twitter_user_from_screen_name(screen_name):
    response = requests.get(f'{TWITTER_CONNECTOR}search/user', params={'screen_name': screen_name})
    if response.status_code != 200:
        print('ERROR', screen_name, response.status_code)
        raise ExternalException(response.status_code, response.json())
    return response.json()

def search_tweets_from_screen_name(screen_name):
    response = requests.get(f'{TWITTER_CONNECTOR}search/tweets', params={'screen_name': screen_name})
    if response.status_code != 200:
        print('ERROR', screen_name, response.status_code)
        raise ExternalException(response.status_code, response.json())
    return response.json()

def search_friends_from_screen_name(screen_name):
    response = requests.get(f'{TWITTER_CONNECTOR}search/friends', params={'screen_name': screen_name})
    if response.status_code != 200:
        print('ERROR', screen_name, response.status_code)
        raise ExternalException(response.status_code, response.json())
    return response.json()

def search_tweets_with_url(url):
    # TODO this is not implemented in twitter_connector
    response = requests.get(f'{TWITTER_CONNECTOR}search/tweets', params={'link': url})
    if response.status_code != 200:
        print('ERROR', url, response.status_code)
        raise ExternalException(response.status_code, response.json())
    return response.json()

def get_tweet(tweet_id):
    response = requests.get(f'{TWITTER_CONNECTOR}tweets/{tweet_id}')
    if response.status_code != 200:
        print('ERROR', tweet_id, response.status_code)
        raise ExternalException(response.status_code, response.json())
    return response.json()



def get_urls_from_tweets(tweets):
    # this method extracts the urls contained in a tweet
    # TODO this method does not belong here
    all_urls = []
    for t in tweets:
        urls = [{'url': u, 'found_in_tweet': str(t['id']), 'retweet': t['retweet']} for u in t['links']]
        all_urls.extend(urls)

    return all_urls