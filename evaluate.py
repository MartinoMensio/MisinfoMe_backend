import data
import json
import os
import multiprocessing
import tqdm

import database

import results
import model
import utils
import twitter
import database

pool_size = 8


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
    reasons = [results.RelationshipReason('contains_url', evaluate_url(url['resolved'])) for url in urls]

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
    return {screen_name: count_user(screen_name, twitter_api, allow_cached, only_cached) for screen_name in screen_names}

def count_user(screen_name, twitter_api, allow_cached, only_cached):
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
    with multiprocessing.Pool(pool_size) as pool:
            classified_urls = []
            for classified in tqdm.tqdm(pool.imap_unordered(data.classify_url, shared_urls), total=len(shared_urls)):
                classified_urls.append(classified)
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
    print(rebuttals_match)
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
        print('evaluating', score, len(verified), len(fake))
    else:
        # default to unknown
        score = 50

    result = {
        'screen_name': screen_name,
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
