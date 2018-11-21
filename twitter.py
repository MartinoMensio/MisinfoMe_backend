import requests
import os
import base64
import json
#from lxml import etree
from bs4 import BeautifulSoup

from twitterscraper.query import query_tweets_from_user

from requests.auth import HTTPBasicAuth
from tqdm import tqdm

import unshortener


def get_bearer_token():
    # these env variables must be there
    tw_key = os.environ['TWITTER_API_KEY']
    tw_secret = os.environ['TWITTER_API_SECRET']
    response = requests.post('https://api.twitter.com/oauth2/token', data={'grant_type': 'client_credentials'}, auth=HTTPBasicAuth(tw_key, tw_secret)).json()
    assert response['token_type'] == 'bearer'
    print('twitter OK')
    return response['access_token']

def get_user_tweets_api(bearer_token, user_handle):
    headers = {'Authorization': 'Bearer {}'.format(bearer_token)}#.format(base64.b64encode(bearer_token.encode('utf-8')))}
    params = {'screen_name': user_handle, 'max_count': 200}
    all_tweets = []
    newest_saved = 0
    cache_file = 'cache/tweets/{}.json'.format(user_handle)
    if os.path.isfile(cache_file):
        with open(cache_file) as f:
            all_tweets = json.load(f)
        newest_saved = max([t['id'] for t in all_tweets])
    while True:
        response = requests.get('https://api.twitter.com/1.1/statuses/user_timeline.json', headers=headers, params=params).json()
        if 'errors' in response or 'error' in response:
            print(response)
            return []

        print('.', end='', flush=True)
        #print(response)
        new_tweets = [t for t in response if t['id'] > newest_saved]
        all_tweets.extend(new_tweets)
        if not len(new_tweets):
            print('done')
            break
        # set the maximum id allowed from the last tweet, and -1 to avoid duplicates
        max_id = new_tweets[-1]['id'] - 1
        params['max_id'] = max_id
    print('retrieved', len(all_tweets), 'tweets')
    with open(cache_file, 'w') as f:
        json.dump(all_tweets, f, indent=2)
    return all_tweets

def get_user_tweets(bearer_token, user_handle):
    list_of_tweets = query_tweets_from_user(user_handle)
    results = [{'entities': {'urls': get_urls_scraper(t)}, 'id': int(t.id)} for t in list_of_tweets]
    return results

def get_urls_scraper(tweet):
    # get from html with BeautifulSoup
    soup = BeautifulSoup(tweet.html, 'html.parser')
    #tree = etree.parse(tweet['html'], htmlparser)
    urls = [{'expanded_url': el['data-expanded-url']} for el in soup.select('a[data-expanded-url]')]
    return urls


def get_urls_from_tweets(tweets, mappings):
    all_urls = []
    for t in tweets:
        urls = [{'url': u['expanded_url'], 'found_in_tweet': t['id']} for u in t['entities']['urls']]
        all_urls.extend(urls)

    uns = unshortener.Unshortener(mappings)
    for url in tqdm(all_urls):
        resolved = uns.unshorten(url['url'])
        url['resolved'] = resolved
    with open('cache/url_mappings.json', 'w') as f:
        json.dump(mappings, f, indent=2)
    return all_urls
