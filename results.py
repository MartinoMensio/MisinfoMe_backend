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
    def __init__(self, type, reasons=[], related=[]):
        # TODO add pointer to self
        self.type = type
        self.related = related
        self.reasons = []
        sum = 0
        count = 0
        for r in reasons:
            if r.related_analysis.score.value != 0:
                self.reasons.append(r)
                weight = scoring_weights[r.related_analysis.type]
                sum += r.related_analysis.score.value * weight
                count += weight
        score = 0
        if count:
            score = sum / count
        self.score = Score(score)


    def to_dict(self):
        # TODO remove all the to_dict crap and rely on JSON serialization of objects
        return {
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
        super().__init__('dataset_match')
        score = 0
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
    def __init__(self, reasons=[], related=[]):
        super().__init__('domain_analysis', reasons, related)

class UrlResult(Result):
    def __init__(self, reasons=[], related=[]):
        super().__init__('url_analysis', reasons, related)

class TweetResult(Result):
    def __init__(self, reasons=[], related=[]):
        super().__init__('tweet_analysis', reasons, related)