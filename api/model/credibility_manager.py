from collections import defaultdict

from ..data import database
from ..external import twitter_connector, credibility_connector
from ..data import utils, unshortener


def get_credibility_weight(credibility):
    """This provides a weight that accounts for:
    - confidence
    - more weight to negative credibility: from 1 (normal) to 100 (for -1)
    """
    credibility_value = credibility['value']
    credibility_confidence = credibility['confidence']

    shame_importance = 1
    if credibility_value < 0:
        shame_importance *= - credibility_value * 100

    return credibility_confidence * shame_importance

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
    tweet_ids = [f"{t['id']}" for t in tweets]
    if not tweets_not_none:
        # no tweets retrieved. Wrong ids or deleted?
        return None
    urls = twitter_connector.get_urls_from_tweets(tweets)
    # let's count the domain appearances in all the tweets
    domains_counts = defaultdict(lambda: 0)
    for url_object in urls:
        url = url_object['url']
        url_unshortened = unshortener.unshorten(url)
        domain = utils.get_url_domain(url_unshortened)
        # TODO URL matches, credibility_connector.get_url_credibility(url_unshortened)
        domains_counts[domain] += 1
    credibility_sum = 0
    confidence_sum = 0
    assessments = []
    domain_assessments = credibility_connector.post_source_credibility_multiple(list(domains_counts.keys()))
    for domain, domain_credibility in domain_assessments.items():
        appearance_cnt = domains_counts[domain]
        print(domain, domain_credibility['credibility'])
        credibility = domain_credibility['credibility']['value']
        confidence = domain_credibility['credibility']['confidence']
        credibility_weight = get_credibility_weight(domain_credibility['credibility'])
        credibility_sum += credibility * credibility_weight * appearance_cnt
        confidence_sum += credibility_weight * appearance_cnt
        assessments.append(domain_credibility)
    if credibility_sum:
        credibility_weighted = credibility_sum / confidence_sum
        confidence_weighted = confidence_sum / len(urls)
    else:
        credibility_weighted = 0.
        confidence_weighted = 0.
    return {
        'credibility': credibility_weighted,
        'confidence': confidence_weighted,
        'assessments': assessments,
        'itemReviewed': tweet_ids # TODO a link to the tweets
    }

def get_user_credibility_from_user_id(user_id):
    tweets = twitter_connector.get_user_tweets(user_id)
    return get_tweets_credibility(tweets)

def get_user_credibility_from_screen_name(screen_name):
    tweets = twitter_connector.search_tweets_from_screen_name(screen_name)
    return get_tweets_credibility(tweets)
