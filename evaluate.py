import data
import json
import os

import database

import results
import model
import utils
import twitter


def save_stats():
    raise NotImplementedError()


def evaluate_domain(url):
    domain = utils.get_url_domain(url)
    print('domain', domain)
    database_object = database.get_domain_info(domain)
    reasons = []
    if not database_object:
        # look also without subdomain
        shorter_domain = utils.get_url_domain_without_subdomains(domain)
        database_object = database.get_domain_info(shorter_domain)
    print('database_object', database_object)
    if database_object:
        # dataset_entry with domain match
        dataset_entry = model.DatasetEntry(database_object)
        print('dataset_entry', dataset_entry.to_dict())
        dataset_match = results.DatasetMatch(dataset_entry)
        print('dataset_match', dataset_match.to_dict())
        rel_reason = results.RelationshipReason('matches', dataset_match)
        reasons.append(rel_reason)
    result = results.DomainResult(reasons)
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
        reasons.append(dataset_match)
    # TODO rebuttals
    result = results.UrlResult(reasons)
    print('result', result.to_dict)
    return result

    if label:
        label['reason'] = 'full URL match'
        label['url'] = url
    else:
        domain = utils.get_url_domain(url)
        label = database.get_domain_info(domain)
        if not label and domain.startswith('www.'):
            # try also without www.
            label = database.get_domain_info(domain[4:])
        if label:
            label['reason'] = 'domain match'
            label['url'] = url
    if label:
        label['found_in_tweet'] = url_info['found_in_tweet']
        label['retweet'] = url_info['retweet']
        #print(label)
    return label

def evaluate_tweet(tweet_id, twitter_api):
    # TODO check tweet_id?
    print(tweet_id)
    tweet_objects = twitter_api.get_statuses_lookup([tweet_id])
    #print('tweet_object', tweet_objects)
    if not tweet_objects:
        return None
    urls = twitter.get_urls_from_tweets(tweet_objects)
    print('urls', urls)
    reasons = [results.RelationshipReason('contains_url', evaluate_url(url['resolved'])) for url in urls]

    result = results.TweetResult(reasons)
    print('result', result.to_dict())
    return result


def count(shared_urls, tweets, handle):
    #matching = [dataset_by_url[el] for el in shared_urls if el in dataset_by_url]
    #verified = [el for el in matching if el['label'] == 'true']
    #fake = [el for el in matching if el['label'] == 'fake']
    results = [data.classify_url(url) for url in shared_urls] # NEED TWEET ID here
    #print(results)
    matching = [el for el in results if el]
    #print(matching)
    verified = [el for el in matching if el['score']['label'] == 'true']
    fake = [el for el in matching if el['score']['label'] == 'fake']
    # rebuttals
    #print(shared_urls)
    rebuttals_match = {claim_url['resolved']: database.get_rebuttals(claim_url['resolved']) for claim_url in shared_urls}
    rebuttals_match = {k:v['rebuttals'] for k,v in rebuttals_match.items() if v}
    print(rebuttals_match)
    you = {
        'tweets_cnt': len(tweets),
        'shared_urls_cnt': len(shared_urls),
        'verified_urls_cnt': len(verified),
        'fake_urls_cnt': len(fake),
        'fake_urls': fake,
        'verified_urls': verified,
        'unknown_urls_cnt': len(shared_urls) - len(matching),
        'rebuttals': rebuttals_match
    }
    if len(tweets) and handle:
        stats[handle] = you
    save_stats()
    sum_over_stats = lambda key: sum([el[key] for el in stats.values()])
    overall = {
        'tweets_cnt': sum_over_stats('tweets_cnt'),
        'shared_urls_cnt': sum_over_stats('shared_urls_cnt'),
        'verified_urls_cnt': sum_over_stats('verified_urls_cnt'),
        'fake_urls_cnt': sum_over_stats('fake_urls_cnt'),
        'unknown_urls_cnt': sum_over_stats('unknown_urls_cnt'),
        'users_cnt': len(stats)
    }
    return {
        'you': you,
        'overall': overall
    }
