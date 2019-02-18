import json
import copy
from collections import defaultdict

import database
import utils
import unshortener

fact_checkers = {el['_id']:el for el in database.get_fact_checkers()}

def classify_url(url_info, unshorten=True):
    url = url_info['url']
    domain = utils.get_url_domain(url)
    if unshorten:
        unshortened_url = unshortener.unshorten(url)
        domain = utils.get_url_domain(unshortened_url)
    else:
        unshortened_url = url
    url_info['resolved'] = unshortened_url
    label_url = database.get_url_info(url)
    if not label_url:
        label_url = database.get_url_info(unshortened_url)
    label_domain = database.get_domain_info(domain)
    if not label_domain and domain.startswith('www.'):
        # try also without www.
        label_domain = database.get_domain_info(domain[4:])

    if label_domain and 'ifcn' in label_domain['score']['sources']:
        label_domain['reason'] = 'fact_checker'
        label_domain['url'] = url
        label = label_domain
        #print('there', label_domain)

    elif label_url:
        label_url['reason'] = 'full_url_match'
        for s in label_url['score']['sources']:
            if s in fact_checkers.keys():
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
            if not dataset.get('name', None):
                # TODO fix that when you understand how to manage fact-checkers as datasets
                # wanted properties to display in frontend: {'name': s, 'url': s}
                dataset = database.get_fact_checker(s)
            label['sources'].append(dataset)
        label['found_in_tweet'] = url_info['found_in_tweet']
        label['retweet'] = url_info['retweet']
        #print(label)
    return label

def get_datasets():
    return [el for el in database.get_datasets()]

def get_domains():
    return [el for el in database.get_domains()]

def get_fact_checkers():
    return [el for el in database.get_fact_checkers()]

def get_domains_vs_datasets_table(create_tsv=False):
    """With create_tsv, this method saves tsv files"""
    datasets = get_datasets()
    domains = get_domains()

    domain_datasets = {}
    n_unique_per_dataset = defaultdict(lambda: 0)
    n_tot_per_dataset = defaultdict(lambda: 0)
    for d in datasets:
        if d['contains'].get('domain_classification', False):
            domain_datasets[d['_id']] = d
    domain_datasets_keys = [k for k in domain_datasets.keys()]

    res = [['domain', 'label'] +[d for d in domain_datasets_keys]]
    for dom in domains:
        line = [dom['_id'], dom['score']['label']]
        available = []
        for dat in domain_datasets_keys:
            classified = dat in dom['score']['sources']
            available.append(classified)
            if(classified):
                n_tot_per_dataset[dat] += 1
        how_many = sum(available)
        #print(how_many)
        if how_many == 1:
            print('just one')
            # just one dataset for that domain
            index = available.index(True)
            dataset_unique = domain_datasets_keys[index]
            print(index, dataset_unique)
            n_unique_per_dataset[dataset_unique] += 1
            print(n_unique_per_dataset)
        line.extend(available)
        res.append(line)

    if create_tsv:
        with open('domains_vs_datasets.tsv', 'w') as f:
            for row in res:
                f.write('\t'.join([str(el) for el in row]) + '\n')

        with open('domains_datasets_uniques.tsv', 'w') as f:
            counts = [['dataset', 'size', '#unique domains']]
            for k, count in n_tot_per_dataset.items():
                n_unique = n_unique_per_dataset[k]
                counts.append([k, count, n_unique])
            for row in counts:
                f.write('\t'.join([str(el) for el in row]) + '\n')

    return res

def get_fact_checkers_table(create_tsv=False):
    fact_checkers = get_fact_checkers()

    properties = ['belongs_to_ifcn', 'uses_claimreview']#, 'valid']

    rows = [['key', 'name', 'url', 'nationality'] + properties]
    for fc in fact_checkers:
        line = [fc['_id'], fc['name'], fc['url'], fc['nationality']]
        line.extend([fc['properties'][p] for p in properties])
        rows.append(line)
    if create_tsv:
        with open('fact_checkers.tsv', 'w') as f:
            for row in rows:
                f.write('\t'.join([str(el) for el in row]) + '\n')

    return rows