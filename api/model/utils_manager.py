from ..data import unshortener
from ..evaluation import evaluate

def unshorten_url(url):
    return {
        'url': url,
        'url_full': unshortener.unshorten(url)
    }

def get_url_published_time(url):
    """returns whe a certain URL has been published"""
    return evaluate.get_url_publish_date(url)
