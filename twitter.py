import requests
import os
import base64

from requests.auth import HTTPBasicAuth

def get_bearer_token():
    # these env variables must be there
    tw_key = os.environ['TWITTER_API_KEY']
    tw_secret = os.environ['TWITTER_API_SECRET']
    response = requests.post('https://api.twitter.com/oauth2/token', data={'grant_type': 'client_credentials'}, auth=HTTPBasicAuth(tw_key, tw_secret)).json()
    assert response['token_type'] == 'bearer'
    print('twitter OK')
    return response['access_token']

def get_user_tweets(bearer_token, user_handle):
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

def get_urls_from_tweets(tweets):
    all_urls = []
    for t in tweets:
        urls = t['entities']['urls']
        all_urls.extend(urls)

    source_urls = [el['expanded_url'] for el in all_urls]

    return source_urls
