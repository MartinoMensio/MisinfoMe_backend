import requests
import os
import base64
import json
#from lxml import etree
from bs4 import BeautifulSoup

from twitterscraper.query import query_tweets_from_user

from requests.auth import HTTPBasicAuth
from tqdm import tqdm

import database
import url_redirect_manager

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
        print('twitter tokens available:', len(self.bearer_tokens))
        self.active = 0

    def get_bearer_token(self, key, secret):
        response = requests.post('https://api.twitter.com/oauth2/token', data={'grant_type': 'client_credentials'}, auth=HTTPBasicAuth(key, secret)).json()
        assert response['token_type'] == 'bearer'
        return response['access_token']

    def _cached_database_list(retrieve_item_from_db_fn, save_item_to_db_fn):
        """
        This decorator avoids querying all the items remotely, using a local database.
        It can be used over a function that has two arguments(self, ids) where ids is a list of id to be retrieved.
        The retrieve_item_from_db_fn is a function with one argument(id) that will try to find the id
        The save_item_to_db_fn is a function with one argument(item) that will save the new elements found by the decorated function.
        """
        def wrap(f):
            def wrapped_f(*args):
                # expand the arguments
                other, ids = args
                # use a dict to manage the merge between the cached values and the ones retrived by the decorated function
                all_results = {}
                # collect there the items that are not in the database yet
                new_ids = []
                for id in ids:
                    item = retrieve_item_from_db_fn(id)
                    if item:
                        # can save to final result
                        all_results[id] = item
                    else:
                        # this has to be retrieved
                        new_ids.append(id)
                # call the decorated function on the reduced list of ids
                print('crazy decorator: already there', len(all_results), 'to be retrieved', len(new_ids))
                new_args = (other, new_ids)
                new_results = f(*new_args)
                # and merge the results in the combined results
                for id, item in zip(new_ids, new_results):
                    all_results[id] = item
                    # saving them in the database too
                    save_item_to_db_fn(item)
                return [all_results[id] for id in ids]
            return wrapped_f
        return wrap

    def _check_rate_limit_exceeded(func):
        """This decorator manages the rate exceeded of the API, switching token and trying again"""
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
            raise Exception('all your twitter credentials have exceeded limits!!!')
        return magic

    def _cursor_request(self, url, headers={}, params={}, partial_field_name='ids'):
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


    def get_user_tweets_from_screen_name(self, screen_name):
        print(screen_name)
        user = self.get_user_from_screen_name(screen_name)
        if not user:
            return []
        return self.get_user_tweets(user['id'])

    def get_user_from_screen_name(self, screen_name):
        user = database.get_twitter_user_from_screen_name(screen_name)
        if not user:
            try:
                user = self.get_user_lookup_from_screen_name(screen_name)
                database.save_twitter_user(user)
            except Exception as e:
                print(e)
                return None

        return user


    def get_user_tweets(self, user_id):
        params = {
            'user_id': user_id,
            'max_count': 200,
            'tweet_mode': 'extended' # to get the full content and all the URLs
        }
        newest_saved = 0
        #print('user id', user['id'])
        all_tweets = list(database.get_tweets_from_user_id(user_id))
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
        response = self._cursor_request('https://api.twitter.com/1.1/followers/ids.json', params=params)
        users = self.get_users_lookup(response)
        return [u['screen_name'] for u in users]

    def get_following(self, user_handle):
        params = {
            'screen_name': user_handle,
            'count': 200
        }
        response = self._cursor_request('https://api.twitter.com/1.1/friends/ids.json', params=params)
        users = self.get_users_lookup(response)
        return [u['screen_name'] for u in users]

    @_cached_database_list(database.get_tweet, database.save_tweet)
    def get_statuses_lookup(self, tweet_ids):
        # TODO docs say to use POST for larger requests
        result = []
        for chunk in split_in_chunks(tweet_ids, 100):
            params = {
                'id': ','.join([str(el) for el in chunk])
            }
            response = self.perform_get({'url': 'https://api.twitter.com/1.1/statuses/lookup.json', 'params': params})
            result.extend(response)
        #print(result)
        return result

    @_cached_database_list(database.get_twitter_user, database.save_twitter_user)
    def get_users_lookup(self, id_list):
        # TODO docs say to use POST for larger requests
        result = []
        for chunk in split_in_chunks(id_list, 100):
            params = {
                'user_id': ','.join([str(el) for el in chunk])
            }
            response = self.perform_get({'url': 'https://api.twitter.com/1.1/users/lookup.json', 'params': params})
            result.extend(response)
        #print(result)
        return result


"""
def get_user_tweets(user_handle):
    list_of_tweets = query_tweets_from_user(user_handle)
    results = [{'entities': {'urls': get_urls_scraper(t)}, 'id': int(t.id), 'id': t.id} for t in list_of_tweets]
    return results

def get_urls_scraper(tweet):
    # get from html with BeautifulSoup
    soup = BeautifulSoup(tweet.html, 'html.parser')
    #tree = etree.parse(tweet['html'], htmlparser)
    urls = [{'expanded_url': el['data-expanded-url']} for el in soup.select('a[data-expanded-url]')]
    return urls
"""



def get_urls_from_tweets(tweets):
    all_urls = []
    for t in tweets:
        urls = [{'url': u['expanded_url'], 'found_in_tweet': str(t['id']), 'tweet_text': t.get('full_text', ''), 'retweet': 'retweeted_status' in t} for u in t['entities']['urls']]
        all_urls.extend(urls)

    for url in tqdm(all_urls):
        url['resolved'] = url_redirect_manager.get_url_redirect_for(url['url'])

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
