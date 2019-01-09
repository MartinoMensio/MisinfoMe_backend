from pymongo import MongoClient

client = MongoClient()
print('database OK')

db = client['test_coinform']

domains_collection = db['domains']
urls_collection = db['urls']
rebuttals_collection = db['rebuttals']
datasets_collection = db['datasets']
fact_checkers_collection = db['fact_checkers']
claimReviews_collection = db['claim_reviews']
url_redirects_collection = db['url_redirects']

def get_domain_info(domain):
    return domains_collection.find_one({'_id': domain})

def get_url_info(url):
    return urls_collection.find_one({'_id': url})

def get_rebuttals(url):
    return rebuttals_collection.find_one({'_id': url})