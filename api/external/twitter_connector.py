import os
import requests

from . import ExternalException
from ..utils import timeit
from ..data import unshortener

TWITTER_CONNECTOR = os.environ.get("TWITTER_CONNECTOR", "http://localhost:20200/")
print("TWITTER_CONNECTOR", TWITTER_CONNECTOR)


def get_twitter_user(user_id):
    response = requests.get(f"{TWITTER_CONNECTOR}users/{user_id}")
    if response.status_code != 200:
        raise ValueError(response.status_code)
    return response.json()


@timeit
def get_user_tweets(user_id):
    response = requests.get(f"{TWITTER_CONNECTOR}users/{user_id}/tweets")
    if response.status_code != 200:
        raise ValueError(response.status_code)
    return response.json()


def search_twitter_user_from_screen_name(screen_name):
    response = requests.get(
        f"{TWITTER_CONNECTOR}search/user", params={"screen_name": screen_name}
    )
    if response.status_code != 200:
        print("ERROR", screen_name, response.status_code)
        raise ExternalException(response)
    return response.json()


@timeit
def search_tweets_from_screen_name(screen_name):
    print(f"getting tweets for {screen_name}")
    response = requests.get(
        f"{TWITTER_CONNECTOR}search/tweets", params={"screen_name": screen_name}
    )
    if response.status_code != 200:
        print("ERROR", screen_name, response.status_code)
        raise ExternalException(response)
    result = response.json()
    print(f"retrieved {len(result)} tweets for {screen_name}")
    return result


@timeit
def search_friends_from_screen_name(screen_name, limit=200):
    response = requests.get(
        f"{TWITTER_CONNECTOR}search/friends",
        params={"screen_name": screen_name, "limit": limit},
    )
    if response.status_code != 200:
        print("ERROR", screen_name, response.status_code)
        raise ExternalException(response)
    return response.json()


@timeit
def search_tweets_with_url(url):
    response = requests.get(f"{TWITTER_CONNECTOR}search/tweets", params={"link": url})
    if response.status_code != 200:
        print("ERROR", url, response.status_code)
        raise ExternalException(response)
    return response.json()


def get_tweet(tweet_id):
    response = requests.get(f"{TWITTER_CONNECTOR}tweets/{tweet_id}")
    if response.status_code != 200:
        print("ERROR", tweet_id, response.status_code)
        raise ExternalException(response)
    return response.json()


def get_urls_from_tweets(tweets):
    """this method extracts the urls contained in a tweet, and also performs unshortening"""
    # TODO this method does not belong here
    all_urls = []
    for t in tweets:
        if not t:
            continue
        urls = [
            {"url": u, "found_in_tweet": str(t["id"]), "retweet": t["retweet"]}
            for u in t["links"]
        ]
        all_urls.extend(urls)

    # TODO unshorten has now improved: use the credibility module
    unshortened = unshortener.unshorten_multiprocess([u["url"] for u in all_urls])
    for url in all_urls:
        url["resolved"] = unshortened[url["url"]]

    return all_urls


def search_twitter_user_from_username_v2(username):
    response = requests.get(
        f"{TWITTER_CONNECTOR}v2/users", params={"username": username}
    )
    if response.status_code != 200:
        print("ERROR", username, response.status_code)
        raise ExternalException(response)
    return response.json()


def search_tweets_from_user_id_v2(user_id, get_all=False, until_id=None):
    response = requests.get(
        f"{TWITTER_CONNECTOR}v2/tweets",
        params={"user_id": user_id, "get_all": get_all, "until_id": until_id},
    )
    if response.status_code != 200:
        print("ERROR", user_id, response.status_code)
        raise ExternalException(response)
    return response.json()


def get_tweet_from_id_v2(tweet_id):
    response = requests.get(f"{TWITTER_CONNECTOR}v2/tweets/{tweet_id}")
    if response.status_code != 200:
        print("ERROR", tweet_id, response.status_code)
        raise ExternalException(response)
    return response.json()


def get_status():
    try:
        response = requests.get(f"{TWITTER_CONNECTOR}utils/status")
    except:
        return {"status": "dead"}
    if response.status_code != 200:
        return {"status": f"HTTP code {response.status_code}"}
    return response.json()
