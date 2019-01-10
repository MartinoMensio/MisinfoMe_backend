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

class TwitterAPI(object):

    def __init__(self):
        # retrieve all the possible twitter API keys and put them in the .env file as TWITTER_KEY_x TWITTER_SECRET_x with x=0,1,2,3,...

        # the set of credentials
        self.credentials = []
        # the set of tokens corresponding to the credentials
        self.bearer_tokens = []
        # which credential is being used
        self.active = 0
        while True:
            key = os.environ.get('TWITTER_KEY_{}'.format(self.active), None)
            if not key:
                break
            secret = os.environ['TWITTER_SECRET_{}'.format(self.active)]
            self.credentials.append({'key': key, 'secret': secret})
            token = self.get_bearer_token(key, secret)
            self.bearer_tokens.append(token)
            self.active += 1
        if not self.bearer_tokens:
            raise ValueError('you don\'t have twitter credentials in the environment!!!')
        self.active = 0

    def get_bearer_token(self, key, secret):
        response = requests.post('https://api.twitter.com/oauth2/token', data={'grant_type': 'client_credentials'}, auth=HTTPBasicAuth(key, secret)).json()
        assert response['token_type'] == 'bearer'
        print('twitter bearer token OK')
        return response['access_token']

    def _check_expiration_decorator(func):
        def magic(self, arg):
            try:
                return func(self, arg)
            except Exception:
                # try with another token
                print('magically trying to handle exception')
                self.active = (self.active + 1) % len(self.bearer_tokens)
                return func(self, arg)
        return magic

    @_check_expiration_decorator
    def get_user_tweets(self, user_handle):
        token = self.bearer_tokens[self.active]
        headers = {'Authorization': 'Bearer {}'.format(token)}#.format(base64.b64encode(bearer_token.encode('utf-8')))}
        params = {
            'screen_name': user_handle,
            'max_count': 200,
            'tweet_mode': 'extended' # to get the full content and all the URLs
        }
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
                return all_tweets

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
        if all_tweets:
            with open(cache_file, 'w') as f:
                json.dump(all_tweets, f, indent=2)
        return all_tweets

    @_check_expiration_decorator
    def get_followers(self, user_handle):
        token = self.bearer_tokens[self.active]
        headers = {'Authorization': 'Bearer {}'.format(token)}#.format(base64.b64encode(bearer_token.encode('utf-8')))}
        params = {
            'screen_name': user_handle,
            'count': 20, # TODO loop over groups of 200
            'cursor': -1
            #'cursor': -1,
        }
        response = requests.get('https://api.twitter.com/1.1/followers/list.json', params=params, headers=headers).json()
        if not 'users' in response:
            return []
        return [u['screen_name'] for u in response['users']]

    @_check_expiration_decorator
    def get_following(self, user_handle):
        token = self.bearer_tokens[self.active]
        headers = {'Authorization': 'Bearer {}'.format(token)}#.format(base64.b64encode(bearer_token.encode('utf-8')))}
        params = {
            'screen_name': user_handle,
            'count': 20, # TODO loop over groups of 200
            'cursor': -1
            #'cursor': -1,
        }
        response = requests.get('https://api.twitter.com/1.1/friends/list.json', params=params, headers=headers).json()
        print(response)
        if not 'users' in response:
            return []
        return [u['screen_name'] for u in response['users']]

    @_check_expiration_decorator
    def get_statuses_lookup(self, tweet_ids):
        token = self.bearer_tokens[self.active]
        headers = {'Authorization': 'Bearer {}'.format(token)}#.format(base64.b64encode(bearer_token.encode('utf-8')))}
        params = {
            'id': tweet_ids
        }
        response = requests.get('https://api.twitter.com/1.1/statuses/lookup.json', params=params, headers=headers).json()
        return response

"""
def get_user_tweets(user_handle):
    list_of_tweets = query_tweets_from_user(user_handle)
    results = [{'entities': {'urls': get_urls_scraper(t)}, 'id': int(t.id), 'id_str': t.id} for t in list_of_tweets]
    return results

def get_urls_scraper(tweet):
    # get from html with BeautifulSoup
    soup = BeautifulSoup(tweet.html, 'html.parser')
    #tree = etree.parse(tweet['html'], htmlparser)
    urls = [{'expanded_url': el['data-expanded-url']} for el in soup.select('a[data-expanded-url]')]
    return urls
"""


def get_urls_from_tweets(tweets, mappings, resolve=False):
    all_urls = []
    for t in tweets:
        urls = [{'url': u['expanded_url'], 'found_in_tweet': t['id_str'], 'retweet': 'retweeted_status' in t} for u in t['entities']['urls']]
        all_urls.extend(urls)

    urls_missing_mapping = [u for u in all_urls if u['url'] not in mappings]
    if resolve:
        # multiprocess
        #"""
        unshortener.unshorten_multiprocess([u['url'] for u in urls_missing_mapping], mappings=mappings)
        for url in all_urls:
            url['resolved'] = mappings[url['url']]
        #"""

        # single process
        """
        uns = unshortener.Unshortener(urls_missing_mapping)
        for url in tqdm(all_urls):
            resolved = uns.unshorten(url['url'])
            url['resolved'] = resolved
        """
    else:
        for url in all_urls:
            url['resolved'] = url['url']

    with open('cache/url_mappings.json', 'w') as f:
        json.dump(mappings, f, indent=2)
    return all_urls
