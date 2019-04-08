from ..data import twitter
from ..data import data
from ..data import database
from ..evaluation import evaluate

# Tweet

def get_tweet_from_id(tweet_id):
    """Returns a single tweet, given its ID or None if it is not retrievable"""
    tweets = get_tweets_from_ids([tweet_id])
    if not tweets:
        return None
    tweet = tweets[0]

    return tweet

def get_tweets_from_ids(tweets_ids):
    """Returns the tweets corresponding to the ids provided"""
    return twitter.get_instance().get_statuses_lookup(tweets_ids)

def get_tweets_from_user_id(user_id, cached_only=False, from_date=None, limit=None, offset=0):
    """Returns a list of tweets given a user_id. cached_only is to avoid searching for newer tweets, from_date limits the search to tweets published after a certain date. limit and offset for paging"""
    return twitter.get_instance().get_user_tweets(user_id)

def get_tweets_from_screen_name(screen_name, cached_only=False, from_date=None, limit=None, offset=0):
    """Returns a list of tweets given a screen_name. cached_only is to avoid searching for newer tweets, from_date limits the search to tweets published after a certain date. limit and offset for paging"""
    return twitter.get_instance().get_user_tweets_from_screen_name(screen_name)

def get_tweets_containing_url(url, cached_only=False, from_date=None, limit=None, offset=0):
    """Returns a list of tweets that contain a certain URL. cached_only is to avoid searching for newer tweets, from_date limits the search to tweets published after a certain date. limit and offset for paging"""
    twitter_api = twitter.get_instance()
    return data.get_tweets_containing_url(url, twitter_api)

# TwitterAccount

def get_twitter_account_from_id(user_id):
    """Returns the twitter account corresponding to the user_id, or None if t is not retrievable"""
    users = get_twitter_accounts_from_ids([user_id])
    if not users:
        return None
    user = users[0]

    return user

def get_twitter_accounts_from_ids(user_ids):
    return twitter.get_instance().get_users_lookup(user_ids)

def get_twitter_account_from_screen_name(screen_name):
    """Returns the twitter account corresponding to the user_id, or None if t is not retrievable"""
    return twitter.get_instance().get_user_from_screen_name(screen_name)

def get_twitter_account_followers_from_id(user_id, limit=None, offset=0):
    """Returns the twitter accounts that follow the specified user"""
    return twitter.get_instance().get_followers(user_id, limit)

def get_twitter_account_friends_from_id(user_id, limit=None, offset=0):
    """Returns the twitter accounts that the specified user is following"""
    return twitter.get_instance().get_following(user_id, limit)

def get_twitter_account_followers_from_screen_name(screen_name, limit=None, offset=0):
    return twitter.get_instance().get_followers_from_screen_name(screen_name, limit)

def get_twitter_account_friends_from_screen_name(screen_name, limit=None, offset=0):
    return twitter.get_instance().get_following_from_screen_name(screen_name, limit)

# FactcheckingOrganisation

def get_factchecking_organisation_from_id(factchecking_organisation_id):
    """Returns the factchecking organisation that corresponds to the specified ID (that is assigned by IFCN)"""
    return data.get_fact_checker(factchecking_organisation_id)

def get_factchecking_organisations(belongs_to_ifcn=True, valid_ifcn=True, country=None):
    """Returns the factchecking organisations that match the criteria parameters: can be True, False or None (no filter)"""
    return data.get_fact_checkers(belongs_to_ifcn, valid_ifcn, country)

# FactcheckingReview

def get_factchecking_review_from_id(factchecking_review_id):
    """Returns the factchecking article that corresponds to the specified ID (assigned internally)"""
    raise NotImplementedError()

def get_factchecking_reviews_from_organisation_id(factchecking_organisation_id, from_date=None):
    """Returns the factchecking reviews that have been published by the specified factchecking organisation"""
    raise NotImplementedError()

def get_factchecking_reviews_at_domain(factchecking_domain, from_date=None):
    """Returns the factchecking reviews that have been published by the specified factchecking domain"""
    raise NotImplementedError()

def get_factchecking_reviews_at_url(publishing_url):
    """Returns the factchecking reviews that have been published at the specified url. It is a many2many between url and reviews"""
    raise NotImplementedError()

def get_factchecking_reviews_by_factchecker():
    return evaluate.get_factchecking_by_factchecker()

# Dataset

def get_dataset_from_id(dataset_id):
    """Returns the dataset corresponding to the id"""
    raise NotImplementedError()

def get_datasets():
    """Returns the information about all the datasets"""
    return [el for el in database.get_datasets()]

def get_data_stats():
    """Returns general data stats"""
    return database.get_collections_stats()

def get_domains():
    return [el for el in database.get_domains()]

def get_factcheckers_table():
    return data.get_fact_checkers_table()
