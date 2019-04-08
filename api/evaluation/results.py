"""
This module contains the definition of the classes for the results
"""

scoring_weights = {
    'dataset_match': 3,
    'domain_analysis': 2,
    'url_analysis': 2,
    'tweet_analysis': 2,
    'text_analysis': 1
}

def _to_dict_nested(v):
    return v if not isinstance(v, str) or not isinstance(v, float) else v.to_dict()

class Result(object):
    def __init__(self, type, resource_url, external_url, description, reasons=[], related=[]):
        # resource_url is the identifier of the result, that corresponds to the endpoint that can be interrogated with a GET to have more info on that
        # external_url is a pointer of the thing in the outside world
        # TODO add pointer to self
        self.type = type
        self.resource_url = resource_url
        self.external_url = external_url
        self.description = description
        self.related = related
        self.reasons = []
        sum = 0
        count = 0
        for r in reasons:
            related_analysis = None
            if isinstance(r, RelationshipReason):
                related_analysis = r.related_analysis
            else:
                raise ValueError(r)
            # the criterion for a valid reason
            #if related_analysis.score.value != 0.:
            if abs(related_analysis.score.value - 0) > 0.01:
                print(related_analysis.score.value)
                self.reasons.append(r)
                weight = scoring_weights[related_analysis.type]
                sum += related_analysis.score.value * weight
                count += weight
        score = 0
        if count:
            score = sum / count
        self.score = Score(score)


    def to_dict(self):
        # TODO remove all the to_dict crap and rely on JSON serialization of objects
        return {
            'resource_url': self.resource_url,
            'external_url': self.external_url,
            'analysis': {
                'type': self.type,
                'score': self.score.to_dict(),
                'reasons': [r.to_dict() for r in self.reasons]
            },
            'related': [r.to_dict() for r in self.related] # TODO use r.to_external_url()
        }

class Reason(object):
    def __init__(self, type):
        self.type = type

    def to_dict(self):
        return {k: _to_dict_nested(v) for k, v in vars(self).items()}

class Score(object):
    def __init__(self, value):
        self.value = float(value)

    def to_dict(self):
        return vars(self)

class RelationshipReason(Reason):
    def __init__(self, relationship_type, destination_reason):
        self.relationship_type = relationship_type
        self.related_analysis = destination_reason
        #self.score = destination_reason.score
        self.type = 'relationship'
        #super().__init__(destination_reason.type)

    """
    def to_dict(self):
        # overwrite the score
        result = super().to_dict()
        result['score'] = self.score.to_dict()
        return result
    """

class DatasetMatch(Result):
    def __init__(self, dataset_entry):
        # TODO dataset_entry should be the class from model.py?
        # TODO check the URLs
        description = 'A record in the dataset'
        super().__init__('dataset_match', '/data/datasets/{}/{}'.format(dataset_entry.type, dataset_entry.key), None, description)
        score = Score(0)
        if dataset_entry.label == 'fake':
            score = Score(-1)
        elif dataset_entry.label == 'true':
            score = Score(1)
        self.score = score
        self.details = dataset_entry

    def to_dict(self):
        result = super().to_dict()
        result['analysis']['details'] = self.details.to_dict()
        return result

class DomainResult(Result):
    def __init__(self, domain, reasons=[], related=[]):
        # TODO check if domain is properly formed with http...
        description = '{}'.format(domain)
        super().__init__('domain_analysis', '/data/domains?domain={}'.format(domain), domain, description, reasons, related)

class UrlResult(Result):
    def __init__(self, url, reasons=[], related=[]):
        description = '{}'.format(url)
        super().__init__('url_analysis', '/data/urls?url={}'.format(url), url, description, reasons, related)

class TweetResult(Result):
    def __init__(self, tweet, reasons=[], related=[]):
        description = '"{}"'.format(tweet.get('full_text', ''))
        super().__init__('tweet_analysis', '/data/tweets/{}'.format(tweet['id']), 'https://twitter.com/statuses/{}'.format(tweet['id']), description, reasons, related)

class UserResult(Result):
    def __init__(self, user, tweet_cnt, reasons=[], related=[]):
        # TODO find better profile URL, using screen name
        description = '{}'.format(user['name'])
        self.tweet_cnt = tweet_cnt
        super().__init__('user_analysis', '/data/user/{}'.format(user['id']), 'https://twitter.com/intent/user?user_id={}'.format(user['id']), description, reasons, related)
