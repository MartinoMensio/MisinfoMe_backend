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

def get_source_credibility(source, update_status_fn=None):
    if update_status_fn:
        update_status_fn('computing the credibility')
    return credibility_connector.get_source_credibility(source)

def get_sources_credibility(sources):
    return credibility_connector.post_source_credibility_multiple(sources)

def get_tweet_credibility_from_id(tweet_id, update_status_fn=None):
    if update_status_fn:
        update_status_fn('retrieving the tweet')
    tweet = twitter_connector.get_tweet(tweet_id)
    if update_status_fn:
        update_status_fn('computing the credibility of the tweet')
    sources_credibility = get_tweets_credibility([tweet])
    urls_credibility = get_tweets_credibility([tweet], group_method='url')

    # TODO: this does not look at the history of the user, just if it has been reviewed directly
    screen_name = tweet['user_screen_name']
    profile_as_source_credibility = credibility_connector.get_source_credibility(f'twitter.com/{screen_name}')

    # profile as source: 20% weight
    # urls in tweet: 60%
    # sources in tweet: 20%
    confidence_weighted = profile_as_source_credibility['credibility']['confidence'] * 0.2 + sources_credibility['credibility']['confidence'] * 0.2 + urls_credibility['credibility']['confidence'] * 0.6
    if confidence_weighted:
        value_weighted = (profile_as_source_credibility['credibility']['value'] * 0.2 * profile_as_source_credibility['credibility']['confidence'] + sources_credibility['credibility']['value'] * 0.2 * sources_credibility['credibility']['confidence']+ urls_credibility['credibility']['value'] * 0.6 * urls_credibility['credibility']['confidence']) / confidence_weighted
    else:
        value_weighted = 0.
    final_credibility = {
        'value': value_weighted,
        'confidence': confidence_weighted
    }

    tweet_id = str(tweet_id)

    result = {
        'credibility': final_credibility,
        'profile_as_source_credibility': profile_as_source_credibility,
        'sources_credibility': sources_credibility,
        'urls_credibility': urls_credibility,
        'itemReviewed': tweet_id,
        'ratingExplanationFormat': 'url',
        'ratingExplanation': f'https://misinfo.me/misinfo/credibility/tweets/{tweet_id}',
    }
    return result

    # print(tweets_credibility)
    # if not tweets_credibility:
    #     return None # error tweets not found
    # return tweets_credibility

def get_tweets_credibility_from_ids(tweet_ids):
    # TODO implement in twitter_connnector batch tweet retrieval
    tweets = [twitter_connector.get_tweet(tweet_id) for tweet_id in tweet_ids]
    sources_credibility = get_tweets_credibility(tweets)
    urls_credibility = get_tweets_credibility(tweets, group_method='url')
    profile_as_source_credibility = {
        'credibility':{
            'value': 0,
            'confidence': 0
        }
    }

    # profile as source: 60% weight
    # urls shared: 25%
    # sources used: 15%
    confidence_weighted = profile_as_source_credibility['credibility']['confidence'] * 0.6 + sources_credibility['credibility']['confidence'] * 0.15 + urls_credibility['credibility']['confidence'] * 0.25
    if confidence_weighted:
        value_weighted = (profile_as_source_credibility['credibility']['value'] * 0.6 * profile_as_source_credibility['credibility']['confidence'] + sources_credibility['credibility']['value'] * 0.15 * sources_credibility['credibility']['confidence']+ urls_credibility['credibility']['value'] * 0.25 * urls_credibility['credibility']['confidence']) / confidence_weighted
    else:
        value_weighted = 0.
    final_credibility = {
        'value': value_weighted,
        'confidence': confidence_weighted
    }

    result = {
        'credibility': final_credibility,
        'profile_as_source_credibility': profile_as_source_credibility,
        'sources_credibility': sources_credibility,
        'urls_credibility': urls_credibility,
        'itemReviewed': tweet_ids
    }
    return result

def get_tweets_credibility(tweets, group_method='domain', update_status_fn=None):
    if update_status_fn:
        update_status_fn('unshortening the URLs contained in the tweets')
    urls = twitter_connector.get_urls_from_tweets(tweets)

    print('retrieving the domains to assess')
    # let's count the group appearances in all the tweets
    groups_appearances = defaultdict(list)
    if group_method == 'domain':
        fn_retrieve_credibility = credibility_connector.post_source_credibility_multiple
    elif group_method == 'source':
        fn_retrieve_credibility = credibility_connector.post_source_credibility_multiple
    elif group_method == 'url':
        fn_retrieve_credibility = credibility_connector.post_url_credibility_multiple
    else:
        raise ValueError(group_method)
    for url_object in urls:
        url_unshortened = url_object['resolved']
        if group_method == 'domain':
            group = utils.get_url_domain(url_unshortened)
        elif group_method == 'source':
            group = utils.get_url_source(url_unshortened)
        elif group_method == 'url':
            group = url_unshortened
        # TODO URL matches, credibility_connector.get_url_credibility(url_unshortened)
        groups_appearances[group].append(url_object['found_in_tweet'])
    credibility_sum = 0
    confidence_sum = 0
    weights_sum = 0
    sources_assessments = []
    print(f'getting credibility for {len(groups_appearances)} groups')
    group_assessments = fn_retrieve_credibility(list(groups_appearances.keys()))
    for group, group_credibility in group_assessments.items():
        appearance_cnt = len(groups_appearances[group])
        credibility = group_credibility['credibility']
        #print(group, credibility)
        credibility_value = credibility['value']
        confidence = credibility['confidence']
        if confidence < 0.1:
            continue
        credibility_weight = get_credibility_weight(credibility_value)
        final_weight = credibility_weight * confidence * appearance_cnt
        credibility_sum += credibility_value * final_weight
        confidence_sum += credibility_weight * confidence * appearance_cnt
        weights_sum += credibility_weight * appearance_cnt
        sources_assessments.append({
            'itemReviewed': group,
            'credibility': credibility,
            'tweets_containing': groups_appearances[group],
            'url': f'/misinfo/credibility/sources/{group}',
            'credibility_weight': credibility_weight,
            'weights': {
                #'origin_weight': origin_weight,
                'final_weight': final_weight
            },
            'assessments': group_credibility['assessments']
        })
    print(f'retrieved credibility for {len(sources_assessments)} groups')
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
    # TODO deprecate, just use the one from screen name
    user = {} #twitter_connector.(user_id)
    raise NotImplementedError('just use get_user_credibility_from_screen_name')
    return get_user_credibility_from_screen_name(user['screen_name'])

def get_user_credibility_from_screen_name(screen_name, update_status_fn=None):
    if update_status_fn:
        update_status_fn('retrieving the information about the profile')
    itemReviewed = twitter_connector.search_twitter_user_from_screen_name(screen_name)
    if update_status_fn:
        update_status_fn('retrieving the tweets from the profile')
    tweets = twitter_connector.search_tweets_from_screen_name(screen_name)
    itemReviewed['tweets_cnt'] = len(tweets)
    if update_status_fn:
        update_status_fn('unshortening the URLs contained in the tweets')
    urls = twitter_connector.get_urls_from_tweets(tweets)
    itemReviewed['shared_urls_cnt'] = len(urls)
    if update_status_fn:
        update_status_fn('computing the credibility of the profile as a source')
    profile_as_source_credibility = credibility_connector.get_source_credibility(f'twitter.com/{screen_name}')
    if update_status_fn:
        update_status_fn('computing the credibility from the sources used in the tweets')
    sources_credibility = get_tweets_credibility(tweets, update_status_fn=update_status_fn)
    if update_status_fn:
        update_status_fn('computing the credibility from the URLs used in the tweets')
    urls_credibility = get_tweets_credibility(tweets, group_method='url', update_status_fn=update_status_fn)




    # profile as source: 60% weight
    # urls shared: 25%
    # sources used: 15%
    confidence_weighted = profile_as_source_credibility['credibility']['confidence'] * 0.6 + sources_credibility['credibility']['confidence'] * 0.15 + urls_credibility['credibility']['confidence'] * 0.25
    if confidence_weighted:
        value_weighted = (profile_as_source_credibility['credibility']['value'] * 0.6 * profile_as_source_credibility['credibility']['confidence'] + sources_credibility['credibility']['value'] * 0.15 * sources_credibility['credibility']['confidence']+ urls_credibility['credibility']['value'] * 0.25 * urls_credibility['credibility']['confidence']) / confidence_weighted
    else:
        value_weighted = 0.
    final_credibility = {
        'value': value_weighted,
        'confidence': confidence_weighted
    }

    result = {
        'credibility': final_credibility,
        'profile_as_source_credibility': profile_as_source_credibility,
        'sources_credibility': sources_credibility,
        'urls_credibility': urls_credibility,
        'itemReviewed': itemReviewed
    }
    database.save_user_credibility_result(itemReviewed['id'], result)
    return result

def get_user_friends_credibility_from_screen_name(screen_name, limit):
    friends = twitter_connector.search_friends_from_screen_name(screen_name, limit)
    results = []
    for f in friends:
        cached = database.get_user_credibility_result(f['id'])
        if cached and 'itemReviewed' in cached.keys():
            result = cached
            result['cache'] = 'hit'
            # TODO proper marshalling
            result['updated'] = str(result['updated'])
            result['screen_name'] = result['itemReviewed']['screen_name']
            # too many details for the friends, removing them
            del result['profile_as_source_credibility']
            del result['sources_credibility']
            del result['urls_credibility']
        else:
            result = {'cache': 'miss', 'screen_name': f['screen_name']}
        results.append(result)
    return results

def get_credibility_origins():
    return credibility_connector.get_origins()
