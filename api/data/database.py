import os
import datetime

from pymongo import MongoClient, errors

MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost:27017')
MONGO_USER = os.environ.get('MONGO_USER', None)
MONGO_PASS = os.environ.get('MONGO_PASS', None)
if MONGO_USER and MONGO_PASS:
    MONGO_URI = 'mongodb://{}:{}@{}'.format(MONGO_USER, MONGO_PASS, MONGO_HOST)
else:
    MONGO_URI = 'mongodb://{}'.format(MONGO_HOST)

print('MONGO_URI', MONGO_URI)

# connect=False allows forking because the connection is opened when needed
client = MongoClient(MONGO_URI, connect=False)
print('database OK')

db_twitter = client['test_coinform']
db_twitter_analysis = client['stored_analysis']
db_redirects = client['utilities']
db_datasets = client['datasets_resources']
db_credibility = client['credibility']

# domain key is the domain itself
domains_collection = db_datasets['domains']
# domain assessments
domain_assessments = db_datasets['domain_assessments']
# url key is the url itself
urls_collection = db_datasets['urls']
# rebuttal key is the url of provenience
rebuttals_collection = db_datasets['rebuttals']
# dataset key is a string defined in sources.json of the repo 'datasets'
sources_collection = db_datasets['sources']
# the same applies to fact_checkers
fact_checkers_collection = db_datasets['fact_checkers']
claimReviews_collection = db_datasets['claim_reviews']
datasets_graph_nodes_collection = db_datasets['graph_nodes']
datasets_graph_links_collection = db_datasets['graph_links']

# fact checking urls (kinda claimReview)
fact_checking_urls = client['datasets_resources']['fact_checking_urls']

#tweets_by_fact_checking = db_twitter_analysis['by_factchecker']
tweets_by_url = db_twitter_analysis['tweets_by_url']

# the key is the url itself
url_redirects_collection = db_redirects['url_redirects']

# the key of a twitter user is the twitter id (long int)
twitter_users = db_twitter['twitter_users']
twitter_tweets = db_twitter['twitter_tweets']


# stored analysis (for stats overall pie chart)
twitter_users_counts = db_twitter_analysis['twitter_users_counts']
twitter_users_credibilities = db_twitter_analysis['twitter_users_credibility']


# credibility collections (NOT USED)
credibility_nodes = db_credibility['nodes']
credibility_computed = db_credibility['computed']



def replace_safe(collection, document, key_property='_id'):
    document['updated'] = datetime.datetime.now()
    # the upsert sometimes fails, mongo does not perform it atomically
    # https://jira.mongodb.org/browse/SERVER-14322
    # https://stackoverflow.com/questions/29305405/mongodb-impossible-e11000-duplicate-key-error-dup-key-when-upserting
    try:
        collection.replace_one({'_id': document[key_property]}, document, upsert=True)
    except errors.DuplicateKeyError:
        collection.replace_one({'_id': document[key_property]}, document, upsert=True)
    document['updated'] = document['updated'].isoformat()

def get_url_redirect(url):
    return url_redirects_collection.find_one({'_id': url})

def save_url_redirect(from_url, to_url):
    url_mapping = {'_id': from_url, 'to': to_url}
    return replace_safe(url_redirects_collection, url_mapping)

def get_url_redirects():
    return url_redirects_collection.find()

def get_url_redirects_in(url_list):
    return url_redirects_collection.find({'_id': {'$in': url_list}})

def get_domain_info(domain):
    return domains_collection.find_one({'_id': domain})

def get_domain_assessments():
    return domain_assessments.find()

def get_url_info(url):
    return urls_collection.find_one({'_id': url})

def get_rebuttals(url):
    return rebuttals_collection.find_one({'_id': url})

def get_tweets_from_user_id(user_id):
    return twitter_tweets.find({'user.id': user_id})

def get_collections_stats():
    return {
        'origins': sources_collection.count(),
        'urls': urls_collection.count(),
        'domains': domains_collection.count(),
        #'rebuttals': rebuttals_collection.count(),
        'fact_checking': fact_checkers_collection.count(),
    }

def get_dataset(dataset_key):
    return sources_collection.find_one({'_id': dataset_key})

def get_fact_checkers():
    return fact_checkers_collection.find()

def get_fact_checker(key):
    return fact_checkers_collection.find_one({'_id': key})

def get_sources():
    return sources_collection.find()

def get_domains():
    return domains_collection.find()

def save_count_result(user_id, count_result):
    count_result['_id'] = int(user_id)
    return replace_safe(twitter_users_counts, count_result)

def get_count_result(user_id):
    return twitter_users_counts.find_one({'_id': int(user_id)})

def get_all_counts():
    return twitter_users_counts.find()

def save_user_credibility_result(user_id, result):
    result['_id'] = int(user_id)
    return replace_safe(twitter_users_credibilities, result)

def get_user_credibility_result(user_id):
    return twitter_users_credibilities.find_one({'_id': int(user_id)})

def get_all_user_credibility():
    return twitter_users_credibilities.find()

def get_all_factchecking():
    return fact_checking_urls.find()

def get_factchecking_from_url(url):
    return fact_checking_urls.find({'url': url})
