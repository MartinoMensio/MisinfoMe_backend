import json
import copy

import database
import utils

def classify_url(url_info):
    url = url_info['resolved']
    label = database.get_url_info(url)
    if label:
        label['reason'] = 'full_url_match'
        label['url'] = url
    else:
        domain = utils.get_url_domain(url)
        label = database.get_domain_info(domain)
        if not label and domain.startswith('www.'):
            # try also without www.
            label = database.get_domain_info(domain[4:])
        if label:
            label['reason'] = 'domain_match'
            label['url'] = url
    if label:
        # attribution of the dataset
        label['sources'] = []
        for s in label['score']['sources']:
            label['sources'].append(database.get_dataset(s))
        label['found_in_tweet'] = url_info['found_in_tweet']
        label['tweet_text'] = url_info['tweet_text']
        label['retweet'] = url_info['retweet']
        #print(label)
    return label
