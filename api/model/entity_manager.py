from ..external import twitter_connector, credibility_connector, claimreview_scraper_connector
from ..data import data
from ..data import database
from ..evaluation import evaluate

# Tweet

def get_tweets_containing_url(url, cached_only=False, from_date=None, limit=None, offset=0):
    """Returns a list of tweets that contain a certain URL. cached_only is to avoid searching for newer tweets, from_date limits the search to tweets published after a certain date. limit and offset for paging"""
    tweets = twitter_connector.search_tweets_with_url(url)
    # TODO check this
    return tweets

# TwitterAccount

def get_twitter_account_from_screen_name(screen_name, cached=False):
    """Returns the twitter account corresponding to the user_id, or None if t is not retrievable"""
    return twitter_connector.search_twitter_user_from_screen_name(screen_name)


def get_twitter_account_friends_from_screen_name(screen_name, limit=None, offset=0):
    # TODO deprecate
    friends = twitter_connector.search_friends_from_screen_name(screen_name)
    return friends

# FactcheckingOrganisation

def get_factchecking_organisation_from_id(factchecking_organisation_id):
    """Returns the factchecking organisation that corresponds to the specified ID (that is assigned by IFCN)"""
    return data.get_fact_checker(factchecking_organisation_id)

def get_factchecking_organisations(belongs_to_ifcn=True, valid_ifcn=True, country=None):
    """Returns the factchecking organisations that match the criteria parameters: can be True, False or None (no filter)"""
    return data.get_fact_checkers(belongs_to_ifcn, valid_ifcn, country)

# FactcheckingReview

def get_factchecking_review_from_id(factchecking_review_id):
    """Returns the factchecking article that corresponds to the specified ID (assigned internally)"""
    raise NotImplementedError()

def get_factchecking_reviews_from_organisation_id(factchecking_organisation_id, from_date=None):
    """Returns the factchecking reviews that have been published by the specified factchecking organisation"""
    raise NotImplementedError()

def get_factchecking_reviews_at_domain(factchecking_domain, from_date=None):
    """Returns the factchecking reviews that have been published by the specified factchecking domain"""
    raise NotImplementedError()

def get_factchecking_reviews_at_url(publishing_url):
    """Returns the factchecking reviews that have been published at the specified url. It is a many2many between url and reviews"""
    raise NotImplementedError()

def get_factchecking_reviews_by_factchecker():
    return evaluate.get_factchecking_by_factchecker()

# Dataset

def get_dataset_from_id(dataset_id):
    """Returns the dataset corresponding to the id"""
    raise NotImplementedError()

def get_origins():
    """Returns the information about all the sources"""
    # TODO refactor sources --> origins
    return [el for el in database.get_sources()]

def get_data_stats():
    """Returns general data stats"""
    return database.get_collections_stats()

def get_domains():
    domains_old_evaluations = [el for el in database.get_domains()]
    domain_names = [el['domain'] for el in domains_old_evaluations]
    # TODO double check to be getting cached evaluations
    credibilities = credibility_connector.post_source_credibility_multiple(domain_names)
    for el in domains_old_evaluations:
        el['credibility'] = credibilities[el['domain']]
    return domains_old_evaluations

def get_factcheckers_table():
    return data.get_fact_checkers_table()

# New MisinfoMe Homepage
def get_most_popular_entries():
    return [
        'BreitbartNews',
        'DailyBuzzLive',
        'newswarz',
        'CRG_CRM',
        'liberty_writers',
        'LawEnforceToday',
        'HenryMakow',
        'LifeZette',
        'Breaking911'
    ]

def get_latest_reviews(max=6):
    # image_url, title, description, fact_check_url
    latest = claimreview_scraper_connector.get_latest_factchecks()
    latest = latest[:max]
    results = []
    for el in latest:
        image_url = f'https://logo.clearbit.com/{el["fact_checker"]["domain"]}'
        title = el['goose']['opengraph'].get('title', None) or el['goose']['title']
        description = el['goose']['opengraph'].get('description', None) or el['goose']['meta']['description']
        fact_check_url = el['review_url']
        date_published = el['date_published']
        results.append({
            'image_url': image_url,
            'title': title,
            'description': description,
            'fact_check_url': fact_check_url,
            'date_published': date_published
        })
    return results

def get_frontend_v2_home():
    return {
        'most_popular_entries': get_most_popular_entries(),
        'stats': {
            'profiles_analysed_count': 2780,
            'tweets_analysed_count': 11750,
            'profiles_misinformed_count': 417,
            'tweets_misinformed_count': 2937
        },
        'latest_reviews': get_latest_reviews(),
    }
