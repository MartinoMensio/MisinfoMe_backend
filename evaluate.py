import data
import json
import os
import multiprocessing
import tqdm
import itertools
from collections import defaultdict
import dateparser

import database

import results
import model
import utils
import twitter
import database

pool_size = 32


def save_stats():
    raise NotImplementedError()


def evaluate_domain(url):
    domain = utils.get_url_domain(url)
    print('domain', domain)
    database_object = database.get_domain_info(domain)
    reasons = []
    if not database_object:
        # look also without subdomain
        domain = utils.get_url_domain_without_subdomains(domain)
        database_object = database.get_domain_info(domain)
    print('database_object', database_object)
    if database_object:
        # dataset_entry with domain match
        dataset_entry = model.DatasetEntry(database_object)
        print('dataset_entry', dataset_entry.to_dict())
        dataset_match = results.DatasetMatch(dataset_entry)
        print('dataset_match', dataset_match.to_dict())
        rel_reason = results.RelationshipReason('matches', dataset_match)
        reasons.append(rel_reason)
    result = results.DomainResult(domain, reasons)
    print('result', result.to_dict())
    return result

def evaluate_url(url):
    # TODO cleanup the URL, lower() the domain part only
    # TODO if it is a tweet url, return the evaluate_tweet
    # TODO if it is a twitter user url, return the evaluate_user
    database_object = database.get_url_info(url)
    print('database_object', database_object)
    rel_reason = results.RelationshipReason('belongs_to_domain', evaluate_domain(url))
    reasons = [rel_reason]
    if database_object:
        # dataset_entry with url match
        dataset_entry = model.DatasetEntry(database_object)
        print('dataset_entry', dataset_entry.to_dict())
        dataset_match = results.DatasetMatch(dataset_entry)
        print('dataset_match', dataset_match.to_dict())
        rel_reason = results.RelationshipReason('matches', dataset_match)
        reasons.append(rel_reason)
    # TODO rebuttals
    result = results.UrlResult(url, reasons)
    print('result', result.to_dict)
    return result

def evaluate_tweet(tweet_id, twitter_api):
    # TODO check tweet_id?
    print('tweet_id', tweet_id)
    tweet_objects = twitter_api.get_statuses_lookup([tweet_id])
    #print('tweet_object', tweet_objects)
    if not tweet_objects:
        return None
    urls = twitter.get_urls_from_tweets(tweet_objects)
    print('urls', urls)
    reasons = [results.RelationshipReason('contains_url', evaluate_url(url['url'])) for url in urls]

    # TODO pass the tweet object instead
    result = results.TweetResult(tweet_objects[0], reasons)
    print('result', result.to_dict())
    return result

def evaluate_twitter_user(user_id, twitter_api):
    # TODO check twitter_id?
    print('user_id', user_id)
    users = twitter_api.get_users_lookup([user_id])
    tweets = twitter_api.get_user_tweets(user_id)
    print('#len tweets', len(tweets))
    reasons = [results.RelationshipReason('writes', evaluate_tweet(tweet['id'], twitter_api)) for tweet in tweets]

    # TODO pass the user object instead
    result = results.UserResult(users[0], len(tweets), reasons)
    return result

def evaluate_twitter_user_from_screen_name(screen_name, twitter_api):
    print('screen_name', screen_name)
    user = twitter_api.get_user_from_screen_name(screen_name)
    if not user:
        return evaluate_twitter_user(None, twitter_api)
    return evaluate_twitter_user(user['id'], twitter_api)


def count_users(screen_names, twitter_api, allow_cached, only_cached):
    return {screen_name: count_user_from_screen_name(screen_name, twitter_api, allow_cached, only_cached) for screen_name in screen_names}

def count_user(user_id, twitter_api, allow_cached, only_cached, multiprocess=True):
    user = twitter_api.get_users_lookup([user_id])[0]
    return count_user_from_screen_name(user['screen_name'], twitter_api, allow_cached, only_cached, multiprocess)

def count_user_from_screen_name(screen_name, twitter_api, allow_cached, only_cached, multiprocess=True):
    user = twitter_api.get_user_from_screen_name(screen_name)
    if not user:
        return {}

    if allow_cached:
        result = database.get_count_result(user['id'])
        if only_cached and not result:
            # null
            return {'cache': 'miss'}
        if result:
            result['cache'] = 'hit'
            return result
    tweets = twitter_api.get_user_tweets(user['id'])
    shared_urls = twitter.get_urls_from_tweets(tweets)
    #matching = [dataset_by_url[el] for el in shared_urls if el in dataset_by_url]
    #verified = [el for el in matching if el['label'] == 'true']
    #fake = [el for el in matching if el['label'] == 'fake']
    #classified_urls = [data.classify_url(url) for url in shared_urls] # NEED TWEET ID here
    if multiprocess:
        with multiprocessing.pool.ThreadPool(pool_size) as pool:
            classified_urls = []
            for classified in tqdm.tqdm(pool.imap_unordered(data.classify_url, shared_urls), total=len(shared_urls)):
                classified_urls.append(classified)
    else:
        classified_urls = [data.classify_url(url) for url in shared_urls]
    matching = [el for el in classified_urls if el]
    #print(matching)
    verified = [el for el in matching if el['score']['label'] == 'true']
    mixed = [el for el in matching if el['score']['label'] == 'mixed']
    fake = [el for el in matching if el['score']['label'] == 'fake']
    # rebuttals
    #print(shared_urls)
    rebuttals_match = {u['resolved']: database.get_rebuttals(u['resolved']) for u in shared_urls}
    rebuttals_match = {k:v['rebuttals'] for k,v in rebuttals_match.items() if v}
    # attach the rebuttal links to the fake urls matching
    #print(rebuttals_match)
    for el in fake:
        rebuttals = rebuttals_match.get(el['url'], None)
        el['rebuttals'] = rebuttals
        #rebuttals_match.pop(f['url'])
    for el in mixed:
        rebuttals = rebuttals_match.get(el['url'], None)
        el['rebuttals'] = rebuttals
    for el in verified:
        rebuttals = rebuttals_match.get(el['url'], None)
        el['rebuttals'] = rebuttals
        #rebuttals_match.pop(f['url'])

    # refactor rebuttals without label
    rebuttals = [{
        'found_in_tweet': 0, # TODO retrieve this, refactor how this method processes tweets
        'retweet': False, # TODO
        'reason': 'rebuttal_match',
        'score': {'label': 'rebuttal'},
        'rebuttals': el_v,
        'url': el_k,
        'sources': [database.get_dataset(s) for ss in el_v for s in ss['source']],
    } for el_k, el_v in rebuttals_match.items()]

    if len(fake) + len(verified):
        score = (50. * (len(verified) - len(fake))) / (len(fake) + len(verified)) + 50
        #print('evaluating', score, len(verified), len(fake))
    else:
        # default to unknown
        score = 50

    result = {
        'screen_name': screen_name,
        'profile_image_url': user['profile_image_url_https'],
        'tweets_cnt': len(tweets),
        'shared_urls_cnt': len(shared_urls),
        'verified_urls_cnt': len(verified),
        'mixed_urls_cnt': len(mixed),
        'fake_urls_cnt': len(fake),
        'unknown_urls_cnt': len(shared_urls) - len(matching),
        'score': score,
        # add after saving to mongo, because rebuttals have dotted keys
        'rebuttals': rebuttals,
        'fake_urls': fake,
        'mixed_urls': mixed,
        'verified_urls': verified
    }


    if len(tweets):
        database.save_count_result(user['id'], result)

    return result

def get_overall_counts():
    counts = database.get_all_counts()
    counts = [el for el in counts]
    score = 50
    if len(counts):
        score = sum(c.get('score', 0) for c in counts) / len(counts)
    return {
        'tweets_cnt': sum(c.get('tweets_cnt', 0) for c in counts),
        'shared_urls_cnt': sum(c.get('shared_urls_cnt', 0) for c in counts),
        'verified_urls_cnt': sum(c.get('verified_urls_cnt', 0) for c in counts),
        'mixed_urls_cnt': sum(c.get('mixed_urls_cnt', 0) for c in counts),
        'fake_urls_cnt': sum(c.get('fake_urls_cnt', 0) for c in counts),
        'unknown_urls_cnt': sum(c.get('unknown_urls_cnt', 0) for c in counts),
        'score': score,
        'twitter_profiles_cnt': len(counts)
    }

def get_factchecking_by_domain():
    all_factchecking = [el for el in database.get_all_factchecking()]
    by_fact_checker_domain = itertools.groupby(sorted(all_factchecking, key=lambda el: utils.get_url_domain_without_www(el['url'])), key=lambda el: utils.get_url_domain_without_www(el['url']))
    by_fact_checker_domain = {k: list(v) for k,v in by_fact_checker_domain}
    result = {}
    # TODO also total stats
    for k, values in by_fact_checker_domain.items():
        urls = set(v['url'] for v in values)
        claim_urls = set(v.get('claim_url', None) for v in values)
        result[k] = {
            'len': len(values),
            'urls_cnt': len(urls),
            'claim_urls_cnt': len(claim_urls),
            #'urls': list(urls),
            #'claim_urls': list(claim_urls)
        }
    return result

def get_factchecking_by_one_domain(domain, twitter_api):
    all_factchecking = [el for el in database.get_all_factchecking()]
    by_fact_checker_domain = itertools.groupby(sorted(all_factchecking, key=lambda el: utils.get_url_domain_without_www(el['url'])), key=lambda el: utils.get_url_domain_without_www(el['url']))
    by_fact_checker_domain = {k: list(v) for k,v in by_fact_checker_domain}
    k = domain
    values = by_fact_checker_domain[k]

    values_with_claim_url = [el for el in values if el.get('claim_url', None)]

    # TODO undeduping urls and claimm_urls

    print('retrieved from dataset')

    overall_counts = {
        'factchecking_urls': len(values),
        'claim_urls': len(values_with_claim_url),
        'factchecking_urls_with_claim_urls': len(values_with_claim_url),
        'factchecking_shares_count': 0,
        'claims_shares_count': 0,
        'by_label': defaultdict(lambda: defaultdict(lambda: 0))
    }
    by_url = []
    urls = set() # TODO this is a temporary solution to avoid duplication of counts
    factchecking_tweets = []
    claim_tweets = []
    for fcu in tqdm.tqdm(values_with_claim_url):
        factchecking_url = fcu['url']
        claim_url = fcu['claim_url']
        print(factchecking_url, claim_url)
        if 'http' not in claim_url:
            # TODO bad data should not arrive here!
            continue

        tweet_ids_sharing_factchecking = data.get_tweets_containing_url(factchecking_url, twitter_api)
        tweet_ids_sharing_claim = data.get_tweets_containing_url(claim_url, twitter_api)

        factchecking_tweets.extend(tweet_ids_sharing_factchecking)
        claim_tweets.extend(tweet_ids_sharing_claim)

        print(factchecking_url)
        by_url.append({
            'factchecking_url': factchecking_url,
            'claim_url': claim_url,
            'factchecking_shares': len(tweet_ids_sharing_factchecking),
            'claim_shares': len(tweet_ids_sharing_claim),
            'label': fcu['label'],
            #'claim_shares_ids': tweet_ids_sharing_claim,
            #'factchecking_shares_ids': tweet_ids_sharing_factchecking
        })
        if not (factchecking_url in urls):
            overall_counts['factchecking_shares_count'] += len(tweet_ids_sharing_factchecking)
            overall_counts['by_label'][fcu['label'] or 'unknown']['factchecking_shares_count'] += len(tweet_ids_sharing_factchecking)
            urls.add(factchecking_url)
        if not (claim_url in urls):
            overall_counts['claims_shares_count'] += len(tweet_ids_sharing_claim)
            overall_counts['by_label'][fcu['label'] or 'unknown']['claims_shares_count'] += len(tweet_ids_sharing_claim)
            urls.add(claim_url)

    """
    urls = set(v['url'] for v in values_with_claim_url)
    urls_shares = {}
    tot_shares = 0
    for url in urls:
        tweets = data.get_tweets_containing_url(url, twitter_api)
        urls_shares[url] = len(tweets)
        tot_shares += len(tweets)

    print('urls done')
    claim_urls = set(v.get('claim_url', None) for v in values_with_claim_url)
    claim_urls_shares = {}
    tot_claim_shares = 0
    for url in claim_urls:
        if url:
            tweets = data.get_tweets_containing_url(url, twitter_api)
            claim_urls_shares[url] = len(tweets)
            tot_claim_shares += len(tweets)
    print('claim_urls done')


    result = {
        'len': len(values),
        'urls_cnt': len(urls),
        'claim_urls_cnt': len(claim_urls),
        'tot_urls_shares': tot_shares,
        'tot_claim_shares': tot_claim_shares,
        'urls': urls_shares,
        'claim_urls': claim_urls_shares
    }
    """
    result = {
        'by_url': by_url,
        'counts': overall_counts,
        'tweet_ids': {
            'sharing_claim': claim_tweets,
            'sharing_factchecking': factchecking_tweets
        }
    }
    return result

def analyse_tweet_time(tweet_ids, time_granularity, mode, reference_time, twitter_api):
    tweet_ids = [int(el) for el in tweet_ids]
    tweets = twitter_api.get_statuses_lookup(tweet_ids)
    print(tweets)
    groups = defaultdict(lambda: 0)
    # TODO fill with 0 in the middle
    for t in tweets:
        created_at = t['created_at']
        print(created_at)
        parsed_date = dateparser.parse(created_at.replace('+0000 ', ''))
        if time_granularity == 'year':
            time_group = '{}'.format(parsed_date.year)
            groups[time_group] += 1
        elif time_granularity == 'month':
            time_group = '{}/{:02d}'.format(parsed_date.year, parsed_date.month)
            groups[time_group] += 1

    results = [{'name': k, 'value': v} for k,v in groups.items()]
    results.sort(key=lambda el: el['name'])

    return results