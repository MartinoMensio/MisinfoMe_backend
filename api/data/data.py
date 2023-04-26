import json
import copy
from collections import defaultdict

from . import database
from . import utils
from . import unshortener
from ..external import twitter_connector


def get_fact_checker(org_id):
    return database.get_fact_checker(org_id)


def get_fact_checkers(belongs_to_ifcn=None, valid_ifcn=None, selected_country=None):
    result = []
    for el in database.get_fact_checkers():
        belonging = el["belongs_to_ifcn"]
        valid = el["valid_ifcn"]
        country = el["nationality"]
        accept = True
        if belongs_to_ifcn != None:
            if belonging != belongs_to_ifcn:
                accept = False
        if valid_ifcn != None:
            if valid != valid_ifcn:
                accept = False
        if selected_country != None:
            if selected_country != country:
                accept = False
        if accept:
            result.append(el)

    return result


def get_tweets_containing_url(url):
    tweets = twitter_connector.search_tweets_with_url(url)

    tweets_ids = [int(el.id) for el in tweets]

    return tweets_ids
