"""
This module describes and manages the model classes.
These classes can be:
- views of database entries (DatasetEntry, Tweet, User)
- objects without persistence (Text, Domain, Url)
- ???
"""

class Entity(object):
    def to_dict(self):
        return vars(self)

class Text(Entity):
    def __init__(self, text):
        self.text = text

class Domain(Entity):
    def __init__(self, domain):
        self.domain = domain

class Url(Entity):
    def __init__(self, url):
        self.url = url

class DatasetEntry(Entity):
    # TODO distinguish between ScoredEntry(url,domains) and UnscoredEntry(rebuttals)
    def __init__(self, dataset_entry):
        """dataset_entry comes from mongodb"""
        self.label = dataset_entry['score']['label']
        self.sources = dataset_entry['score']['sources']
        self.key = dataset_entry['_id']
        if 'domain' in dataset_entry:
            self.type = 'domain_entry'
        elif 'url' in dataset_entry:
            self.type = 'url_entry'
        # TODO textual claims entries

class Tweet(Entity):
    def __init__(self, tweet):
        """The tweet comes from mongodb"""
        self.id = tweet['id']
        self.text = tweet['full_text']
        self.user_id = tweet['user']['id']

class User(Entity):
    def __init__(self, user):
        """The user comes from mongodb"""
        self.id = user['id']
        self.screen_name = user['screen_name']
        self.name = user['name']