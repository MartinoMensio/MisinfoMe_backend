import json
import os
import multiprocessing
import tqdm
import itertools
from collections import defaultdict
import dateparser
import datetime
from dateutil.relativedelta import relativedelta


from . import results, model
from ..data import utils, twitter, database, data

pool_size = 32


def save_stats():
    raise NotImplementedError()

### Tree evaluations: with reasons

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

### Count methods: just counting tweets, need refactoring

def count_users(user_ids, twitter_api, allow_cached, only_cached):
    return [count_user(user_id, twitter_api, allow_cached, only_cached) for user_id in user_ids]

def count_users_from_screen_name(screen_names, twitter_api, allow_cached, only_cached):
    return [count_user_from_screen_name(screen_name, twitter_api, allow_cached, only_cached) for screen_name in screen_names]

def count_user(user_id, twitter_api, allow_cached, only_cached, multiprocess=True):
    users = twitter_api.get_users_lookup([user_id])
    if not users:
        return None
    user = users[0]
    return count_user_from_screen_name(user['screen_name'], twitter_api, allow_cached, only_cached, multiprocess)

def count_user_from_screen_name(screen_name, twitter_api, allow_cached, only_cached, multiprocess=True):
    print(allow_cached, only_cached)
    user = twitter_api.get_user_from_screen_name(screen_name)
    if not user or 'id' not in user:
        # TODO handle other status codes (user not existent or suspended, with error code and message)
        return {'screen_name': screen_name}

    if allow_cached:
        result = database.get_count_result(user['id'])
        if only_cached and not result:
            # null
            return {'_id': user['id'], 'screen_name': screen_name, 'cache': 'miss'}
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

### Methods for grouping database entries

def get_factchecking_by_domain():
    """grouped by domain of factchecking, better to use by_factchecker (see below)"""
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

def get_factchecking_by_factchecker():
    all_factchecking = [el for el in database.get_all_factchecking()]
    fact_checkers = [el for el in database.get_fact_checkers()]

    result = {el['domain']: {
        'name': el['name'],
        'fact_checking': []
    } for el in fact_checkers}

    by_fact_checker_domain = itertools.groupby(sorted(all_factchecking, key=lambda el: utils.get_url_domain_without_www(el['url'])), key=lambda el: utils.get_url_domain_without_www(el['url']))
    by_fact_checker_domain = {k: list(v) for k,v in by_fact_checker_domain}

    for k,v in result.items():
        domain_name = utils.get_url_domain_without_www(k)
        v['domain'] = domain_name

        # group by finding
        fact_checking_matching = []
        for k2, v2 in by_fact_checker_domain.items():
            if domain_name in k2:
                fact_checking_matching.extend(v2)
        fact_checking_urls = {el['url'] for el in fact_checking_matching}
        fact_checking_matching_with_claim_url = [el for el in fact_checking_matching if el.get('claim_url', None)]
        claim_urls = {el['url'] for el in fact_checking_matching_with_claim_url}
        v['claim_urls_cnt'] = len(claim_urls)
        v['factchecking_urls_cnt'] = len(fact_checking_urls)

    return result
    """
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
    """

#def get_factchecking_by_one_factchecker(factchecker, twitter_api)

def get_factchecking_by_one_domain(domain, twitter_api, time_granularity='month'):
    all_factchecking = [el for el in database.get_all_factchecking()]
    by_fact_checker_domain = itertools.groupby(sorted(all_factchecking, key=lambda el: utils.get_url_domain_without_www(el['url'])), key=lambda el: utils.get_url_domain_without_www(el['url']))
    by_fact_checker_domain = {k: list(v) for k,v in by_fact_checker_domain}
    values = []
    for k2, v2 in by_fact_checker_domain.items():
            if domain in k2:
                values.extend(v2)

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
    factchecking_tweets_relative = defaultdict(lambda: 0)
    claim_tweets_relative = defaultdict(lambda: 0)
    for fcu in tqdm.tqdm(values_with_claim_url):
        factchecking_url = fcu['url']
        claim_url = fcu['claim_url']
        print(factchecking_url, claim_url)
        if 'http' not in claim_url:
            # TODO bad data should not arrive here!
            continue

        analyse_url_distribution(factchecking_url, twitter_api)
        tweet_ids_sharing_factchecking = data.get_tweets_containing_url(factchecking_url, twitter_api)
        tweet_ids_sharing_claim = data.get_tweets_containing_url(claim_url, twitter_api)

        factchecking_tweets.extend(tweet_ids_sharing_factchecking)
        claim_tweets.extend(tweet_ids_sharing_claim)

        """
        TODO this section has to be moved in another part, callable to obtain the plot
        for k, v in analyse_tweet_time_relative(fcu, tweet_ids_sharing_factchecking, time_granularity, twitter_api).items():
            factchecking_tweets_relative[k] += v

        for k, v in analyse_tweet_time_relative(fcu, tweet_ids_sharing_claim, time_granularity, twitter_api).items():
            claim_tweets_relative[k] += v
        """


        #print(factchecking_url)
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
        },
        'relative_time': {
            'factchecking': factchecking_tweets_relative,
            'claim': claim_tweets_relative
        }
    }
    return result

def analyse_url_distribution(url, twitter_api, reference_date=None, time_granularity='month'):
    tweet_ids_sharing = data.get_tweets_containing_url(url, twitter_api)
    if reference_date:
        # this analysis is time relative to reference
        tweets_relative = defaultdict(lambda: 0)
        for k, v in analyse_tweet_time_relative(None, tweet_ids_sharing, time_granularity, twitter_api).items():
            tweets_relative[k] += v
        result = tweets_relative
    else:
        # absolute analysis
        result = analyse_tweet_time(tweet_ids_sharing, time_granularity, 'absolute', None, twitter_api)

    return result

def get_url_publish_date(url):
    matching = database.get_factchecking_from_url(url)
    results = []
    for m in matching:
        date_str = m.get('date')
        if date_str:
            debunking_time = dateparser.parse(date_str).date()
            results.append(debunking_time)
    if not results:
        return None
    # some articles get updated, we want the lowest publication time
    publishing_date = min(results)
    return {
        'date': publishing_date.strftime('%d/%m/%Y'),
        'round_month': round_date(publishing_date, 'month'),
        'round_week': round_date(publishing_date, 'week'),
        'round_day': round_date(publishing_date, 'day'),
    }


def analyse_tweet_time_relative(fact_checking_url, tweet_ids, time_granularity, twitter_api):
    date_str = fact_checking_url.get('date')
    if date_str:
        debunking_time = dateparser.parse(date_str)
        #print('date found')
    else:
        #print(fact_checking_url)
        #print('date not found')
        return {}
    tweet_ids = [int(el) for el in tweet_ids]
    tweets = twitter_api.get_statuses_lookup(tweet_ids)
    groups = defaultdict(lambda: 0)
    for t in tweets:
        created_at = t['created_at']
        #print(created_at)
        parsed_date = dateparser.parse(created_at.replace('+0000 ', ''))
        time_interval = parsed_date - debunking_time
        if time_granularity == 'year':
            time_group = time_interval.days // 365
            #time_group = parsed_date.year
            groups[time_group] += 1
        elif time_granularity == 'month':
            time_group = time_interval.days * 12 // 365
            #time_group = parsed_date.year * 12 + parsed_date.month
            groups[time_group] += 1
        elif time_granularity == 'week':
            time_group = time_interval // 7
            groups[time_group] += 1

    #print(groups)
    return groups

def analyse_tweet_time(tweet_ids, time_granularity, mode, reference_time, twitter_api):
    tweet_ids = [int(el) for el in tweet_ids]
    print(tweet_ids)
    tweets = twitter_api.get_statuses_lookup(tweet_ids)
    #print(tweets)
    groups = defaultdict(lambda: 0)
    # fill with 0 in the middle
    min_date = None
    max_date = None
    for t in tweets:
        created_at = t['created_at']
        #print(created_at)
        parsed_date = dateparser.parse(created_at.replace('+0000 ', ''))
        if not min_date:
            min_date = parsed_date
        if not max_date:
            max_date = parsed_date
        min_date = min([min_date, parsed_date])
        max_date = max([max_date, parsed_date])
        time_group = round_date(parsed_date, time_granularity)
        groups[time_group] += 1

    # filling with 0
    curr_date = min_date
    while curr_date and curr_date < max_date:
        group = round_date(curr_date, time_granularity)
        groups[group] # this will populate the group because of defaultdict

        if time_granularity == 'day':
            curr_date += datetime.timedelta(days=1)
        elif time_granularity == 'week':
            curr_date += datetime.timedelta(weeks=1)
        elif time_granularity == 'month':
            curr_date += relativedelta(months=1)


    results = [{'name': k, 'value': v} for k,v in groups.items()]
    results.sort(key=lambda el: el['name'])

    return results

def round_date(date, time_granularity):
    if time_granularity == 'year':
        time_group = '{}'.format(date.year)
    elif time_granularity == 'month':
        time_group = '{}/{:02d}'.format(date.year, date.month)
    elif time_granularity == 'week':
        time_group = '{}/w{:02}'.format(date.isocalendar()[0], date.isocalendar()[1])
    elif time_granularity == 'day':
        time_group = '{}/{:02d}/{:02d}'.format(date.year, date.month, date.day)
    return time_group
