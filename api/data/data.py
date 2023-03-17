import json
import copy
from collections import defaultdict

from . import database
from . import utils
from . import unshortener
from ..external import twitter_connector

# fact_checkers = {el['_id']:el for el in database.get_fact_checkers()}

def get_datasets():
    return [el for el in database.get_sources()]

def get_domains():
    return [el for el in database.get_domains()]

def get_fact_checker(org_id):
    return database.get_fact_checker(org_id)

def get_fact_checkers(belongs_to_ifcn=None, valid_ifcn=None, selected_country=None):
    result = []
    for el in database.get_fact_checkers():
        belonging = el['belongs_to_ifcn']
        valid = el['valid_ifcn']
        country = el['nationality']
        accept = True
        if belongs_to_ifcn != None:
            if belonging != belongs_to_ifcn:
                accept = False
        if valid_ifcn != None:
            if valid != valid_ifcn:
                accept = False
        if selected_country != None:
            if selected_country != country:
                accept = False
        if accept:
            result.append(el)

    return result


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

    properties = ['belongs_to_ifcn', 'valid_ifcn']#, 'uses_claimreview']

    rows = [['key', 'name', 'url', 'nationality'] + properties]
    for fc in fact_checkers:
        line = [fc['_id'], fc['name'], fc['url'], fc['nationality']]
        line.extend([fc[p] for p in properties])
        rows.append(line)
    if create_tsv:
        with open('fact_checkers.tsv', 'w') as f:
            for row in rows:
                f.write('\t'.join([str(el) for el in row]) + '\n')

    return rows

def get_tweets_containing_url(url):
    tweets = twitter_connector.search_tweets_with_url(url)

    tweets_ids = [int(el.id) for el in tweets]

    return tweets_ids