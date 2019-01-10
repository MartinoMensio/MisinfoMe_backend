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
import database

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

    def _check_rate_limit_exceeded(func):
        def magic(self, arg):
            retries_available = len(self.bearer_tokens)
            while retries_available:
                try:
                    return func(self, arg)
                except ValueError as e:
                    if str(e) == '88':
                        # try with another token
                        print('magically trying to handle exception')
                        retries_available -= 1
                        self.active = (self.active + 1) % len(self.bearer_tokens)
                    else:
                        # not my problem!
                        raise e

        return magic

    def _cursor_request(self, url, headers={}, params={}, partial_field_name='id'):
        """
        This function handles cursored requests, combining the partial results and giving back the combined result
        Cursored requests are followers/ids, friends/ids
        partial_field_name is the name of the field where the partial results are.
        This function overwrites the params['cursor']
        """

        total_response = []
        params['cursor'] = -1
        while params['cursor'] != 0:
            try:
                response = self.perform_get({'url': url, 'headers': headers, 'params': params})
            except:
                # some errors like private profile
                break
            params['cursor'] = response['next_cursor']
            total_response.extend(response[partial_field_name])

        return total_response

    @_check_rate_limit_exceeded
    def perform_get(self, parameters):
        """
        Parameters must contain the URL and the URL parameters:
        {'url': URL, 'params': {k: v of PARAMS}, 'headers': {k,v of HEADERS}}
        The header Authorization is retrieved from the self.bearer_tokens, so it will be overwritten
        This function is decorated so that on rate exceeded a new bearer token will be used
        """
        print(parameters)
        token = self.bearer_tokens[self.active]
        url = parameters['url']
        headers = parameters.get('headers', {})
        headers = {'Authorization': 'Bearer {}'.format(token)}
        params = parameters['params']
        response = requests.get(url, headers=headers, params=params).json()
        if 'errors' in response:
            for error in response['errors']:
                if error['code'] == 88:
                    # rate limit exceeded, this is catched by the decorator
                    raise ValueError(88)
        if 'errors' in response or 'error' in response:
            raise Exception(response)

        return response

    def get_user_lookup_from_screen_name(self, screen_name):
        return self.perform_get({'url': 'https://api.twitter.com/1.1/users/show.json', 'params': {'screen_name': screen_name}})


    def get_user_tweets(self, user_handle):
        print(user_handle)
        user = database.get_twitter_user_from_screen_name(user_handle)
        if not user:
            try:
                user = self.get_user_lookup_from_screen_name(user_handle)
                database.save_twitter_user(user)
            except Exception as e:
                print(e)
                return []
        params = {
            'user_id': user['id_str'],
            'max_count': 200,
            'tweet_mode': 'extended' # to get the full content and all the URLs
        }
        newest_saved = 0
        #print('user id', user['id_str'])
        all_tweets = list(database.get_tweets_from_user_id(user['id_str']))
        #print('tweets found', len(all_tweets))
        if all_tweets:
            newest_saved = max([t['id'] for t in all_tweets])
        while True:
            try:
                response = self.perform_get({'url': 'https://api.twitter.com/1.1/statuses/user_timeline.json', 'params': params})
            except Exception as e:
                print(e)
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
            database.save_new_tweets(all_tweets)
        return all_tweets

    def get_followers(self, user_handle):
        params = {
            'screen_name': user_handle,
            'count': 200 # TODO loop over groups of 200
        }
        response = self._cursor_request('https://api.twitter.com/1.1/followers/ids.json', params=params, partial_field_name='users')
        users = self.get_users_lookup(response)
        return [u['screen_name'] for u in users]

    def get_following(self, user_handle):
        params = {
            'screen_name': user_handle,
            'count': 200
        }
        response = self._cursor_request('https://api.twitter.com/1.1/friends/ids.json', params=params, partial_field_name='users')
        users = self.get_users_lookup(response)
        return [u['screen_name'] for u in users]

    def get_statuses_lookup(self, tweet_ids):
        # TODO docs say to use POST for larger requests
        result = []
        for chunk in split_in_chunks(tweet_ids, 100):
            params = {
                'id': ','.join(chunk)
            }
            response = self.perform_get({'url': 'https://api.twitter.com/1.1/statuses/lookup.json', 'params': params})
            result.extend(response)
        #print(result)
        return result

    def get_users_lookup(self, id_list):
        # TODO docs say to use POST for larger requests
        result = []
        for chunk in split_in_chunks(id_list, 100):
            params = {
                'user_id': ','.join(chunk)
            }
            response = self.perform_get({'url': 'https://api.twitter.com/1.1/users/lookup.json', 'params': params})
            result.extend(response)
        #print(result)
        return result


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

def split_in_chunks(iterable, chunk_size):
    for i in range(0, len(iterable), chunk_size):
        yield iterable[i:i+chunk_size]


def save_cached_to_db():
    """Migration function"""
    import glob
    import tqdm
    for file in tqdm.tqdm(glob.glob('cache/tweets/*')):
        with open(file) as f:
            content = json.load(f)
        for t in content:
            database.save_tweet(t)
