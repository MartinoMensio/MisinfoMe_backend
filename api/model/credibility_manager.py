from collections import defaultdict
from tqdm import tqdm

from ..data import database
from ..external import twitter_connector, credibility_connector, ExternalException
from ..data import utils, unshortener


def get_credibility_weight(credibility_value):
    """This provides a weight that gives more weight to negative credibility: from 1 (normal) to 100 (for -1)"""

    result = 1
    if credibility_value < 0:
        result *= - credibility_value * 100

    return result

# Source credibility

def get_source_credibility(source, update_status_fn=None):
    """Obtain the credibility score for a single source"""
    if update_status_fn:
        update_status_fn('computing the credibility')
    return credibility_connector.get_source_credibility(source)

def get_sources_credibility(sources):
    """Obtain the credibility score for multiple sources"""
    return credibility_connector.post_source_credibility_multiple(sources)



# Tweet credibility

def get_tweet_credibility_from_id(tweet_id, update_status_fn=None):
    if update_status_fn:
        update_status_fn('retrieving the tweet')
    try:
        exception = None
        tweet = twitter_connector.get_tweet(tweet_id)
    except ExternalException as e:
        # tweet may have been deleted
        tweet = {
            'id': str(tweet_id),
            'text': None,
            'retweet': None,
            'retweet_source_tweet': None,
            'links': [],
            'user_id': None,
            'user_screen_name': None,
            'exception': vars(e)
        }
        exception = dict(vars(e))
        exception_real = e
    if update_status_fn:
        update_status_fn('computing the credibility of the tweet')
    sources_credibility = get_tweets_credibility([tweet])
    urls_credibility = get_tweets_credibility([tweet], group_method='url')
    tweet_direct_credibility = get_tweets_credibility_directly_reviewed(tweet)

    # TODO: this does not look at the history of the user, just if it has been reviewed directly
    screen_name = tweet['user_screen_name']
    profile_as_source_credibility = credibility_connector.get_source_credibility(f'twitter.com/{screen_name}')

    # profile as source: 20% weight
    # urls in tweet: 60%
    # sources in tweet: 20%
    # tweet_direct_credibility takes over if it exists
    if tweet_direct_credibility['credibility']['confidence'] > 0.01:
        confidence_weighted = tweet_direct_credibility['credibility']['confidence']
        value_weighted = tweet_direct_credibility['credibility']['value']
        tweet_direct = True
    else:
        tweet_direct = False
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

    # TODO if tweet was removed, and we have some fact-checks, retrieve the user handle to show the other components of the score (credibility_as_source)

    misinfome_frontend_url = f'https://misinfo.me/misinfo/credibility/tweets/{tweet_id}'
    result = {
        'credibility': final_credibility,
        'profile_as_source_credibility': profile_as_source_credibility,
        'sources_credibility': sources_credibility,
        'urls_credibility': urls_credibility,
        'itemReviewed': tweet_id,
        'ratingExplanationFormat': 'url',
        'ratingExplanation': misinfome_frontend_url,
        'exception': exception,
    }
    if tweet_direct_credibility['credibility']['confidence'] > 0.01:
        result['tweet_direct_credibility'] = tweet_direct_credibility

    if exception and not tweet_direct:
        raise exception_real

    # explanation (TODO enable)
    explanation = get_credibility_explanation(result, screen_name)
    result['ratingExplanation'] = explanation
    result['ratingExplanationFormat'] = 'markdown'

    return result



def get_credibility_explanation(rating, screen_name):
    tweet_id = rating['itemReviewed']
    misinfome_frontend_url = f'https://misinfo.me/misinfo/credibility/tweets/{tweet_id}'
    tweet_link = f'https://twitter.com/a/statuses/{tweet_id}'
    # TODO manage cases when multiple situations apply (sort by confidence the different conditions)
    if 'tweet_direct_credibility' in rating:
        # Situation 1: the tweet has been fact-checked
        # TODO manage multiple reviews, agreeing and disagreeing
        tweet_rating = rating['tweet_direct_credibility']['assessments'][0]['reports'][0]
        factchecker_label = tweet_rating['coinform_label'].replace('_', ' ')
        factchecker_name = tweet_rating['origin']['name']
        factchecker_assessment = tweet_rating['origin']['assessment_url']
        factchecker_report_url = tweet_rating['report_url']
        explanation = f'This [tweet]({tweet_link}) has been fact-checked as **{factchecker_label}** ' \
                      f'by [{factchecker_name}]({factchecker_assessment}). ' \
                      f'See their report [here]({factchecker_report_url}). ' \
                      f'\n\nFor more details of this analysis, [visit MisinfoMe]({misinfome_frontend_url})'''
    elif rating['urls_credibility']['credibility']['confidence'] > 0.01:
        # Situation 2: the tweet contains a link that was reviewed
        # TODO manage multiple URLs
        # TODO manage multiple reviews, agreeing and disagreeing
        # TODO provide source name??
        url_rating = rating['urls_credibility']['assessments'][0]['assessments'][0]['reports'][0]
        url_reviewed = 'TODO'
        factchecker_label = url_rating['coinform_label'].replace('_', ' ')
        factchecker_name = url_rating['origin']['name']
        factchecker_assessment = url_rating['origin']['assessment_url']
        factchecker_report_url = url_rating['report_url']
        explanation = f'This [tweet]({tweet_link}) contains a link fact-checked as **{factchecker_label}** ' \
                    f'by [{factchecker_name}]({factchecker_assessment}). ' \
                    f'See their report [here]({factchecker_report_url}). ' \
                    f'\n\nFor more details of this analysis, [visit MisinfoMe]({misinfome_frontend_url})'''
    elif rating['sources_credibility']['credibility']['confidence'] > 0.2:
        # Situation 3: the tweet contains a link that comes from a source that is not credible
        source_evaluations = rating['sources_credibility']['assessments']
        # TODO manage multiple sources rated
        # TODO manage multiple reviews, agreeing and disagreeing
        source = source_evaluations[0]['itemReviewed']
        not_factchecking_report = [el for el in source_evaluations[0]['assessments'] if el['origin_id'] != 'factchecking_report']
        print(not_factchecking_report)
        tools = sorted(not_factchecking_report, key=lambda el: el['weights']['final_weight'], reverse=True)[:3]
        factchecking_report = [el for el in source_evaluations[0]['assessments'] if el['origin_id'] == 'factchecking_report']
        if factchecking_report:
            factchecking_report = factchecking_report[0]
            # TODO fact-checks may also be true!!!! In this case the list filtered by not_credible will become empty
            reports = factchecking_report['reports']
            # dict removes duplicates
            print(reports)
            # origin is null if not a proper fact-checker
            factcheckers = {el['origin']['id']: el['origin'] for el in reports if (el['coinform_label'] == 'not_credible' and el['origin'])}
            # create markdown for each one of them
            factcheckers_names = [el["name"] for el in factcheckers.values()]
            factcheckers_names = [f'[{el["name"]}]({el["assessment_url"]})' for el in factcheckers.values()]
            additional_explanation_factchecking = f'*{source}* also contains false claims according to {", ".join(factcheckers_names)}. '
        else:
            additional_explanation_factchecking = ''
        # TODO tools have evaluation URLs, maybe it's better than linking to the homepage?
        tool_names = ', '.join(f"[{el['origin']['name']}]({el['origin']['homepage']})" for el in tools)
        label = get_coinform_label(rating['sources_credibility']['credibility'])
        explanation = f'This [tweet]({tweet_link}) contains a link to *{source}* which is a **{label.replace("_", " ")}** source ' \
                      f'according to {tool_names}. ' \
                      f'{additional_explanation_factchecking}' \
                      f'\n\nFor more details of this analysis, [visit MisinfoMe]({misinfome_frontend_url})'
    elif rating['profile_as_source_credibility']['credibility']['confidence'] > 0.01:
        # Situation 4: the tweet comes from a non-credible profile
        profile_link = rating['profile_as_source_credibility']['itemReviewed']
        profile_name = profile_link.split('/')[-1] # (the same as screenName)
        # profile_link = f'https://twitter.com/{profile_name}'
        assessments = rating['profile_as_source_credibility']['assessments']
        factchecking_report = [el for el in assessments if el['origin_id'] == 'factchecking_report']
        reports = factchecking_report[0]['reports']
        # TODO count by tweet reviewed, not by factchecker URL!!!
        misinfo_from_profile_cnt = len(set(el['report_url'] for el in reports if el['coinform_label'] == 'not_credible'))
        goodinfo_from_profile_cnt = len(set(el['report_url'] for el in reports if el['coinform_label'] == 'credible'))
        uncertain_from_profile_cnt = len(set(el['report_url'] for el in reports if el['coinform_label'] == 'uncertain'))
        if misinfo_from_profile_cnt:
            stats_piece = f'misinformation other {misinfo_from_profile_cnt} times'
        elif uncertain_from_profile_cnt:
            stats_piece = f'uncertain informations other {uncertain_from_profile_cnt} times'
        else:
            stats_piece = f'verified information other {goodinfo_from_profile_cnt} times' 
        explanation = f'This [tweet]({tweet_link}) comes from [{profile_name}]({profile_link}), ' \
                      f'a profile that has shared {stats_piece}. ' \
                      f'\n\nFor more details of this analysis, [visit MisinfoMe]({misinfome_frontend_url})'
    else:
        explanation = f'We could not find any verified information regarding the credibility of this [tweet]({tweet_link}).' \
                      f'\n\nFor more details of this analysis, [visit MisinfoMe]({misinfome_frontend_url})'

    return explanation


def get_coinform_label(credibility):
    label = 'not_verifiable'
    if credibility['confidence'] >= 0.5:
        if credibility['value'] > 0.6:
            label = 'credible'
        elif credibility['value'] > 0.25:
            label = 'mostly_credible'
        elif credibility['value'] >= -0.25:
            label = 'uncertain'
        else:
            label = 'not_credible'
    return label
    # print(tweets_credibility)
    # if not tweets_credibility:
    #     return None # error tweets not found
    # return tweets_credibility

# def get_tweets_credibility_from_ids(tweet_ids): # NOT CALLED ANYWHERE
#     # TODO implement in twitter_connnector batch tweet retrieval
#     tweets = [twitter_connector.get_tweet(tweet_id) for tweet_id in tweet_ids]
#     sources_credibility = get_tweets_credibility(tweets)
#     urls_credibility = get_tweets_credibility(tweets, group_method='url')
#     # tweet_direct_credibility = get_tweets_credibility_directly_reviewed(tweet)
#     profile_as_source_credibility = {
#         'credibility':{
#             'value': 0,
#             'confidence': 0
#         }
#     }

#     # profile as source: 60% weight
#     # urls shared: 25%
#     # sources used: 15%
#     confidence_weighted = profile_as_source_credibility['credibility']['confidence'] * 0.6 + sources_credibility['credibility']['confidence'] * 0.15 + urls_credibility['credibility']['confidence'] * 0.25
#     if confidence_weighted:
#         value_weighted = (profile_as_source_credibility['credibility']['value'] * 0.6 * profile_as_source_credibility['credibility']['confidence'] + sources_credibility['credibility']['value'] * 0.15 * sources_credibility['credibility']['confidence']+ urls_credibility['credibility']['value'] * 0.25 * urls_credibility['credibility']['confidence']) / confidence_weighted
#     else:
#         value_weighted = 0.
#     final_credibility = {
#         'value': value_weighted,
#         'confidence': confidence_weighted
#     }

#     result = {
#         'credibility': final_credibility,
#         'profile_as_source_credibility': profile_as_source_credibility,
#         'sources_credibility': sources_credibility,
#         'urls_credibility': urls_credibility,
#         'itemReviewed': tweet_ids
#     }
#     return result

def get_tweets_credibility_directly_reviewed(tweet):
    # TODO how to deal with username change to search for tweet credibility?
    tweet_url = f'https://twitter.com/{tweet["user_screen_name"]}/status/{tweet["id"]}'
    result = credibility_connector.get_url_credibility(tweet_url)
    return result

def get_tweets_credibility(tweets, group_method='domain', update_status_fn=None):
    # TODO remove `group_method` param, do both 'domain' and 'source' together?
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



# User credibility

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
    # get_tweets_credibility_directly_reviewed data is already in `profile_as_source_credibility`




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


# Credibility origins
def get_credibility_origins():
    return credibility_connector.get_origins()
