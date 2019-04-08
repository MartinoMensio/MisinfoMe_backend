from ..evaluation import evaluate
from ..data import twitter

def analyse_url(url, allow_cached=False, only_cached=False):
    pass

def analyse_tweet(tweet_id, allow_cached=False, only_cached=False):
    pass

def analyse_twitter_account(twitter_id, allow_cached=True, only_cached=False):
    twitter_api = twitter.get_instance()
    return evaluate.count_user(twitter_id, twitter_api, allow_cached, only_cached)

def analyse_twitter_account_from_screen_name(twitter_screen_name, allow_cached=True, only_cached=False):
    twitter_api = twitter.get_instance()
    return evaluate.count_user_from_screen_name(twitter_screen_name, twitter_api, allow_cached, only_cached)

def analyse_twitter_accounts(twitter_ids, allow_cached=True, only_cached=True):
    twitter_api = twitter.get_instance()
    return evaluate.count_users(twitter_ids, twitter_api, allow_cached, only_cached)

def analyse_twitter_accounts_from_screen_name(twitter_screen_names, allow_cached=True, only_cached=True):
    twitter_api = twitter.get_instance()
    return evaluate.count_users_from_screen_name(twitter_screen_names, twitter_api, allow_cached, only_cached)