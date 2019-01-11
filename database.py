from pymongo import MongoClient

client = MongoClient()
print('database OK')

db = client['test_coinform']

# domain key is the domain itself
domains_collection = db['domains']
# url key is the url itself
urls_collection = db['urls']
# rebuttal key is the url of provenience
rebuttals_collection = db['rebuttals']
# dataset key is a string defined in sources.json of the repo 'datasets'
datasets_collection = db['datasets']
# the same applies to fact_checkers
fact_checkers_collection = db['fact_checkers']
claimReviews_collection = db['claim_reviews']
# the key is the url itself
url_redirects_collection = db['url_redirects']

# the key of a twitter user is the twitter id (long int)
twitter_users = db['twitter_users']
twitter_tweets = db['twitter_tweets']

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
