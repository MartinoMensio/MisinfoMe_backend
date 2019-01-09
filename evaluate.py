import data
import json
import os

import database

# this variable keeps the evaluations for each user. Persistence on disk
stats = {}
stats_file = 'cache/stats.json'
if os.path.isfile(stats_file):
    with open(stats_file) as f:
        stats = json.load(f)

def save_stats():
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

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
