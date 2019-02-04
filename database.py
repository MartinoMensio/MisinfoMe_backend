import os

from pymongo import MongoClient

MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost:27017')
MONGO_USER = os.environ.get('MONGO_USER', None)
MONGO_PASS = os.environ.get('MONGO_PASS', None)
if MONGO_USER and MONGO_PASS:
    MONGO_URI = 'mongodb://{}:{}@{}'.format(MONGO_USER, MONGO_PASS, MONGO_HOST)
else:
    MONGO_URI = 'mongodb://{}'.format(MONGO_HOST)

client = MongoClient(MONGO_URI)
print('database OK')

db_twitter = client['test_coinform']
db_twitter_analysis = client['test_coinform']
db_redirects = client['test_coinform']
db_datasets = client['datasets_resources']

# domain key is the domain itself
domains_collection = db_datasets['domains']
# url key is the url itself
urls_collection = db_datasets['urls']
# rebuttal key is the url of provenience
rebuttals_collection = db_datasets['rebuttals']
# dataset key is a string defined in sources.json of the repo 'datasets'
datasets_collection = db_datasets['datasets']
# the same applies to fact_checkers
fact_checkers_collection = db_datasets['fact_checkers']
claimReviews_collection = db_datasets['claim_reviews']

# the key is the url itself
url_redirects_collection = db_redirects['url_redirects']

# the key of a twitter user is the twitter id (long int)
twitter_users = db_twitter['twitter_users']
twitter_tweets = db_twitter['twitter_tweets']


# stored analysis (for stats overall pie chart)
twitter_users_counts = db_twitter_analysis['twitter_users_counts']



def get_url_redirect(url):
    return url_redirects_collection.find_one({'_id': url})

def save_url_redirect(from_url, to_url):
    url_mapping = {'_id': from_url, 'to': to_url}
    return url_redirects_collection.replace_one({'_id': url_mapping['_id']}, url_mapping, upsert=True)

def get_url_redirects():
    return url_redirects_collection.find()

def get_url_redirects_in(url_list):
    return url_redirects_collection.find({'_id': {'$in': url_list}})

def get_domain_info(domain):
    return domains_collection.find_one({'_id': domain})

def get_url_info(url):
    return urls_collection.find_one({'_id': url})

def get_rebuttals(url):
    return rebuttals_collection.find_one({'_id': url})

def save_twitter_user(user):
    user['_id'] = user['id']
    return twitter_users.replace_one({'_id': user['_id']}, user, upsert=True)

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
    return twitter_tweets.replace_one({'_id': tweet['_id']}, tweet, upsert=True)

def save_new_tweets(tweets):
    to_save = []
    for t in tweets:
        if '_id' not in t:
            t['_id'] = t['id']
            to_save.append(t)
    print(len(to_save))
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
        'urls': urls_collection.count(),
        'domains': domains_collection.count(),
        'rebuttals': rebuttals_collection.count(),
        'datasets': datasets_collection.count()
    }

def get_dataset(dataset_key):
    return datasets_collection.find_one({'_id': dataset_key})

def get_datasets():
    return datasets_collection.find()

def get_domains():
    return domains_collection.find()

def save_count_result(user_id, count_result):
    count_result['_id'] = user_id
    return twitter_users_counts.replace_one({'_id': count_result['_id']}, count_result, upsert=True)

def get_count_result(user_id):
    return twitter_users_counts.find_one({'_id': user_id})

def get_all_counts():
    return twitter_users_counts.find()
