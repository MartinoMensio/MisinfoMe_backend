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

client = MongoClient(MONGO_URI)
print('database OK')

db_twitter = client['test_coinform']
db_twitter_analysis = client['stored_analysis']
db_redirects = client['test_coinform']
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


# credibility collections
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

def save_twitter_user(user):
    user['_id'] = user['id']
    return replace_safe(twitter_users, user)

def save_twitter_users(users):
    for u in users:
        u['_id'] = u['id']
    return twitter_users.insert_many(users)

def get_twitter_user(id):
    return twitter_users.find_one({'_id': id})

def get_twitter_user_from_screen_name(screen_name):
    return twitter_users.find_one({'screen_name': screen_name})

def save_tweet(tweet):
    tweet['_id'] = tweet['id']
    return replace_safe(twitter_tweets, tweet)

def save_new_tweets(tweets):
    to_save = []
    for t in tweets:
        if '_id' not in t:
            t['_id'] = t['id']
            to_save.append(t)
    if to_save:
        return twitter_tweets.insert_many(to_save)
    else:
        return True

def get_tweet(id):
    return twitter_tweets.find_one({'_id': id})

def get_tweets_from_user_id(user_id):
    return twitter_tweets.find({'user.id': user_id})

def get_collections_stats():
    return {
        'sources': sources_collection.count(),
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
    count_result['_id'] = user_id
    return replace_safe(twitter_users_counts, count_result)

def get_count_result(user_id):
    return twitter_users_counts.find_one({'_id': user_id})

def get_all_counts():
    return twitter_users_counts.find()

def get_users_id():
    return twitter_users.find(projection={'_id': True})

def get_all_factchecking():
    return fact_checking_urls.find()

def get_factchecking_from_url(url):
    return fact_checking_urls.find({'url': url})


"""
def save_tweets_relevant_factchecking(factchecking_domain, tweets):
    item = tweets
    item['_id'] = factchecking_domain
    return tweets_by_fact_checking.insert(item)

def get_tweets_relevant_factchecking(factchecking_domain):
    return tweets_by_fact_checking.find_one(factchecking_domain)
"""

def get_tweets_by_url(url):
    return tweets_by_url.find_one({'_id': url})

def save_tweets_by_url(url, tweets):
    document = {'_id': url, 'url': url, 'tweets': tweets, 'updated': datetime.datetime.now()}
    return tweets_by_url.replace_one({'_id': document['_id']}, document, upsert=True)



def credibility_add_node(node_id, node):
    document = node
    document['_id'] = node_id
    return credibility_nodes.insert_one(document)

def credibility_remove_node(node_id):
    return credibility_nodes.delete_one({'_id': node_id})

def credibility_get_nodes():
    return credibility_nodes.find()

def credibility_get_outgoing_links_from_node_id(node_id):
    return db_credibility[node_id].find()

def credibility_reset():
    return client.drop_database('credibility')

def credibility_add_link(source_id, dest_id, link):
    print(source_id, dest_id, link)
    document = link
    document['from'] = source_id
    document['to'] = dest_id
    # TODO check source_id and dest_id exist
    return db_credibility[source_id].insert_one(document)

def get_dataset_graph():
    nodes = datasets_graph_nodes_collection.find()
    links = datasets_graph_links_collection.find()
    return {
        'nodes': {n['id']: n for n in nodes},
        'links': [l for l in links]
    }
