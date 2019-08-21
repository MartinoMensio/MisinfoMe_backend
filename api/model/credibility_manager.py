from collections import defaultdict
from tqdm import tqdm

from ..data import database
from ..external import twitter_connector, credibility_connector
from ..data import utils, unshortener


def get_credibility_weight(credibility_value):
    """This provides a weight that gives more weight to negative credibility: from 1 (normal) to 100 (for -1)"""

    result = 1
    if credibility_value < 0:
        result *= - credibility_value * 100

    return result

def get_source_credibility(source):
    return credibility_connector.get_source_credibility(source)

def get_tweet_credibility_from_id(tweet_id):
    tweet = twitter_connector.get_tweet(tweet_id)
    tweets_credibility = get_tweets_credibility([tweet])
    print(tweets_credibility)
    if not tweets_credibility:
        return None # error tweets not found
    return tweets_credibility

def get_tweets_credibility_from_ids(tweet_ids):
    # TODO implement in twitter_connnector batch tweet retrieval
    tweets = [twitter_connector.get_tweet(tweet_id) for tweet_id in tweet_ids]
    return get_tweets_credibility(tweets)

def get_tweets_credibility(tweets):
    tweets_not_none = [t for t in tweets if t]
    if not tweets_not_none:
        # no tweets retrieved. Wrong ids or deleted?
        return None
    urls = twitter_connector.get_urls_from_tweets(tweets_not_none)

    print('retrieving the domains to assess')
    # let's count the domain appearances in all the tweets
    domains_appearances = defaultdict(list)
    for url_object in urls:
        url_unshortened = url_object['resolved']
        domain = utils.get_url_domain(url_unshortened)
        # TODO URL matches, credibility_connector.get_url_credibility(url_unshortened)
        domains_appearances[domain].append(url_object['found_in_tweet'])
    credibility_sum = 0
    confidence_sum = 0
    weights_sum = 0
    sources_assessments = []
    print(f'getting credibility for {len(domains_appearances)} domains')
    domain_assessments = credibility_connector.post_source_credibility_multiple(list(domains_appearances.keys()))
    for domain, domain_credibility in domain_assessments.items():
        appearance_cnt = len(domains_appearances[domain])
        credibility = domain_credibility['credibility']
        #print(domain, credibility)
        credibility_value = credibility['value']
        confidence = credibility['confidence']
        credibility_weight = get_credibility_weight(credibility_value)
        credibility_sum += credibility_value * credibility_weight * confidence * appearance_cnt
        confidence_sum += credibility_weight * confidence * appearance_cnt
        weights_sum += credibility_weight * appearance_cnt
        sources_assessments.append({
            'itemReviewed': domain,
            'credibility': credibility,
            'tweets_containing': domains_appearances[domain],
            'url': f'/misinfo/credibility/sources/{domain}',
            'credibility_weight': credibility_weight
        })
    print(f'retrieved credibility for {len(sources_assessments)} domains')
    if credibility_sum:
        credibility_weighted = credibility_sum / confidence_sum
        confidence_weighted = confidence_sum / weights_sum
    else:
        credibility_weighted = 0.
        confidence_weighted = 0.
    return {
        'credibility': {
            'value': credibility_weighted,
            'confidence': confidence_weighted
        },
        'assessments': sources_assessments##{
            #'sources': sources_assessments, # here matches at the source-level
            #'documents': [], # here matches at the document-level
            #'claims': [] # here matches at the claim-level
        #},
        #'itemReviewed': tweet_ids # TODO a link to the tweets
    }

def get_user_credibility_from_user_id(user_id):
    tweets = twitter_connector.get_user_tweets(user_id)
    return get_tweets_credibility(tweets)

def get_user_credibility_from_screen_name(screen_name):
    tweets = twitter_connector.search_tweets_from_screen_name(screen_name)
    return get_tweets_credibility(tweets)

def get_credibility_origins():
    return credibility_connector.get_origins()
