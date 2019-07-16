import os
import requests

TWITTER_ENDPOINT = os.environ.get('TWITTER_ENDPOINT', 'http://localhost:20200')
print('TWITTER_ENDPOINT', TWITTER_ENDPOINT)

def get_twitter_user(user_id):
    response = requests.get(f'{TWITTER_ENDPOINT}/users/{user_id}')
    if response.status_code != 200:
        raise ValueError(response.status_code)
    return response.json()

def get_user_tweets(user_id):
    response = requests.get(f'{TWITTER_ENDPOINT}/users/{user_id}/tweets')
    if response.status_code != 200:
        raise ValueError(response.status_code)
    return response.json()

def search_twitter_user_from_screen_name(screen_name):
    response = requests.get(f'{TWITTER_ENDPOINT}/search/user', params={'screen_name': screen_name})
    if response.status_code != 200:
        print('ERROR', screen_name, response.status_code)
        return None
    return response.json()

def search_tweets_from_screen_name(screen_name):
    response = requests.get(f'{TWITTER_ENDPOINT}/search/tweets', params={'screen_name': screen_name})
    if response.status_code != 200:
        raise ValueError(response.status_code)
    return response.json()

def search_friends_from_screen_name(screen_name):
    response = requests.get(f'{TWITTER_ENDPOINT}/search/friends', params={'screen_name': screen_name})
    if response.status_code != 200:
        print('ERROR', screen_name, response.status_code)
        return None
    return response.json()


def get_urls_from_tweets(tweets):
    all_urls = []
    for t in tweets:
        urls = [{'url': u, 'found_in_tweet': str(t['id']), 'retweet': t['retweet']} for u in t['links']]
        all_urls.extend(urls)

    return all_urls