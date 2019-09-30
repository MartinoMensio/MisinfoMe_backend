import json
import os
import tqdm
import itertools
from collections import defaultdict
import dateparser
import datetime
from dateutil.relativedelta import relativedelta


from ..data import utils, database, data
from ..external import twitter_connector
from ..model import credibility_manager

pool_size = 32


def save_stats():
    raise NotImplementedError()

### Count methods: just counting tweets, need refactoring

def count_user(user, tweets, allow_cached, only_cached, use_credibility):
    # print(user['screen_name'], allow_cached, only_cached)
    if not user or 'id' not in user:
        # TODO handle other status codes (user not existent or suspended, with error code and message)
        return {'screen_name': user['screen_name']}
    if allow_cached:
        if use_credibility:
            result = database.get_user_credibility_result(user['id'])
        else:
            result = database.get_count_result(user['id'])
        if only_cached and not result:
            # null
            return {'_id': user['id'], 'screen_name': user['screen_name'], 'cache': 'miss'}
        if result:
            result['cache'] = 'hit'
            return result
    print('going to evaluate', user['screen_name'])
    shared_urls = twitter_connector.get_urls_from_tweets(tweets)

    print('classifiying urls')
    classified_urls = classify_urls(shared_urls, use_credibility)

    matching = [el for el in classified_urls if el]
    #print(matching)
    verified = [el for el in matching if el['score']['label'] == 'true']
    mixed = [el for el in matching if el['score']['label'] == 'mixed']
    fake = [el for el in matching if el['score']['label'] == 'fake']
    # # rebuttals
    # #print(shared_urls)
    # rebuttals_match = {u['resolved']: database.get_rebuttals(u['resolved']) for u in shared_urls}
    # rebuttals_match = {k:v['rebuttals'] for k,v in rebuttals_match.items() if v}
    # # attach the rebuttal links to the fake urls matching
    # #print(rebuttals_match)
    # for el in fake:
    #     rebuttals = rebuttals_match.get(el['url'], None)
    #     el['rebuttals'] = rebuttals
    #     #rebuttals_match.pop(f['url'])
    # for el in mixed:
    #     rebuttals = rebuttals_match.get(el['url'], None)
    #     el['rebuttals'] = rebuttals
    # for el in verified:
    #     rebuttals = rebuttals_match.get(el['url'], None)
    #     el['rebuttals'] = rebuttals
    #     #rebuttals_match.pop(f['url'])

    # # refactor rebuttals without label
    # rebuttals = [{
    #     'found_in_tweet': 0, # TODO retrieve this, refactor how this method processes tweets
    #     'retweet': False, # TODO
    #     'reason': 'rebuttal_match',
    #     'score': {'label': 'rebuttal'},
    #     'rebuttals': el_v,
    #     'url': el_k,
    #     'sources': [database.get_dataset(s) for ss in el_v for s in ss['source']],
    # } for el_k, el_v in rebuttals_match.items()]

    if len(fake) + len(verified):
        score = (50. * (len(verified) - len(fake))) / (len(fake) + len(verified)) + 50
        #print('evaluating', score, len(verified), len(fake))
    else:
        # default to unknown
        score = 50

    result = {
        'screen_name': user['screen_name'],
        'profile_image_url': user['image'],
        'tweets_cnt': len(tweets),
        'shared_urls_cnt': len(shared_urls),
        'verified_urls_cnt': len(verified),
        'mixed_urls_cnt': len(mixed),
        'fake_urls_cnt': len(fake),
        'unknown_urls_cnt': len(shared_urls) - len(matching),
        'score': score,
        # add after saving to mongo, because rebuttals have dotted keys
        'rebuttals': [],#rebuttals,
        'fake_urls': fake,
        'mixed_urls': mixed,
        'verified_urls': verified
    }

    # last step: save in the database
    if len(tweets):
        if use_credibility:
            database.save_user_credibility_result(user['id'], result)
        else:
            database.save_count_result(user['id'], result)

    print(user['screen_name'], 'done')
    return result

# def count_users(user_ids, twitter_api, allow_cached, only_cached, use_credibility):
#     return [count_user(user_id, twitter_api, allow_cached, only_cached, use_credibility) for user_id in user_ids]

# def count_users_from_screen_name(screen_names, twitter_api, allow_cached, only_cached, use_credibility):
#     return [count_user_from_screen_name(screen_name, twitter_api, allow_cached, only_cached, use_credibility) for screen_name in screen_names]



def classify_urls(urls_info, use_credibility):
    if use_credibility:
        return classify_urls_credibility(urls_info)
    else:
        return classify_urls_legacy(urls_info)

def classify_urls_credibility(urls_info):
    """Classifies the URLs based on the new credibility model, but replies in a legacy-compatible way"""
    urls_to_domains = {el['resolved']: utils.get_url_domain(el['resolved']) for el in urls_info}
    domains_credibility = credibility_manager.get_sources_credibility(list(set(urls_to_domains.values())))

    result = []
    for url_info in urls_info:
        url = url_info['resolved']
        #print(url_info)
        domain = urls_to_domains[url]

        # TODO doing one by one is extremely slow
        domain_credibility = domains_credibility[domain]
        credibility_value = domain_credibility['credibility']['value']
        if abs(domain_credibility['credibility']['confidence']) < 0.2:
            print('unknown', domain)
            label = None
        else:
            label = {
                'domain': domain,
                'score': {
                    'label': 'true' if (credibility_value > 0.4) else ('fake' if (credibility_value < -0.4) else 'mixed')
                },
                'reason': 'domain_match',
                'url': url,
                'found_in_tweet': url_info['found_in_tweet'],
                'retweet': url_info['retweet'],
                'sources': [{
                    '_id': origin['origin_id'],
                    'name': origin['origin_id'], # TODO better (via joining data)
                    'url': origin['url'],
                    'type': 'domain_list'
                } for origin in domain_credibility['assessments']]
        }
        result.append(label)
    return result

def classify_urls_legacy(urls_info):
    """The legacy evaluation"""
    result = []
    for url_info in tqdm.tqdm(urls_info):
        #print(url_info)
        result.append(classify_url_legacy(url_info))
    return result

def classify_url_legacy(url_info):
    url = url_info['resolved']
    domain = utils.get_url_domain(url)

    label_url = database.get_url_info(url)
    label_domain = database.get_domain_info(domain)

    if not label_domain and domain.startswith('www.'):
        # try also without www.
        label_domain = database.get_domain_info(domain[4:])

    if label_domain and label_domain['score'].get('is_fact_checker', False):
        label_domain['reason'] = 'fact_checker'
        label_domain['url'] = url
        label = label_domain
        #print('there', label_domain)

    elif label_url:
        label_url['reason'] = 'full_url_match'
        for s in label_url['score']['sources']:
            if s in data.fact_checkers.keys():
                label_url['reason'] = 'fact_checking'
                label_url['score']['sources'] = [s]
                break
        label_url['url'] = url
        label = label_url

    else:
        if label_domain:
            label_domain['reason'] = 'domain_match'
            label_domain['url'] = url
            label = label_domain
        else:
            label = None

    if label:
        # attribution of the dataset
        label['sources'] = []
        for s in label['score']['sources']:
            dataset = database.get_dataset(s)
            if not dataset:
                #print('WARNING: not found', s)
                continue
            if not dataset.get('name', None):
                # TODO fix that when you understand how to manage fact-checkers as datasets
                # wanted properties to display in frontend: {'name': s, 'url': s}
                dataset = database.get_fact_checker(s)
            label['sources'].append(dataset)
        label['found_in_tweet'] = url_info['found_in_tweet']
        label['retweet'] = url_info['retweet']
        #print(label)
    return label



### Methods for grouping database entries

def get_factchecking_by_domain():
    """grouped by domain of factchecking, better to use by_factchecker (see below)"""
    all_factchecking = [el for el in database.get_all_factchecking()]
    by_fact_checker_domain = itertools.groupby(sorted(all_factchecking, key=lambda el: utils.get_url_domain_without_subdomains(el['url'])), key=lambda el: utils.get_url_domain_without_subdomains(el['url']))
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

    by_fact_checker_domain = itertools.groupby(sorted(all_factchecking, key=lambda el: utils.get_url_domain_without_subdomains(el['url'])), key=lambda el: utils.get_url_domain_without_subdomains(el['url']))
    by_fact_checker_domain = {k: list(v) for k,v in by_fact_checker_domain}

    for k,v in result.items():
        domain_name = utils.get_url_domain_without_subdomains(k)
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

def get_factchecking_by_one_domain(domain, time_granularity='month'):
    all_factchecking = [el for el in database.get_all_factchecking()]
    by_fact_checker_domain = itertools.groupby(sorted(all_factchecking, key=lambda el: utils.get_url_domain_without_subdomains(el['url'])), key=lambda el: utils.get_url_domain_without_subdomains(el['url']))
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

        analyse_url_distribution(factchecking_url)
        tweet_ids_sharing_factchecking = data.get_tweets_containing_url(factchecking_url)
        tweet_ids_sharing_claim = data.get_tweets_containing_url(claim_url)

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

def analyse_url_distribution(url, reference_date=None, time_granularity='month'):
    tweet_ids_sharing = data.get_tweets_containing_url(url)
    if reference_date:
        # this analysis is time relative to reference
        tweets_relative = defaultdict(lambda: 0)
        for k, v in analyse_tweet_time_relative(None, tweet_ids_sharing, time_granularity).items():
            tweets_relative[k] += v
        result = tweets_relative
    else:
        # absolute analysis
        result = analyse_tweet_time(tweet_ids_sharing, time_granularity, 'absolute', None)

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


def analyse_tweet_time_relative(fact_checking_url, tweet_ids, time_granularity):
    date_str = fact_checking_url.get('date')
    if date_str:
        debunking_time = dateparser.parse(date_str)
        #print('date found')
    else:
        #print(fact_checking_url)
        #print('date not found')
        return {}
    tweet_ids = [int(el) for el in tweet_ids]
    tweets = [twitter_connector.get_tweet(t_id) for t_id in tweet_ids]
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

def analyse_tweet_time(tweet_ids, time_granularity, mode, reference_time):
    tweet_ids = [int(el) for el in tweet_ids]
    print(tweet_ids)
    tweets = [twitter_connector.get_tweet(t_id) for t_id in tweet_ids]
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
