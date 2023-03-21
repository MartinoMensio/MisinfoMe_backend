# this endpoint is for updating the datasets
from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..external import claimreview_scraper_connector, credibility_connector

router = APIRouter()

class StatsBody(BaseModel):
    date: str


@router.post('/update')
def update_data(body: StatsBody):
    json_data = body.json()
    print(json_data)
    a = credibility_connector.update_origin('ifcn')
    print(a)
    date = body.date
    b = claimreview_scraper_connector.download_data(date)
    print(b)
    c = credibility_connector.update_origin('factchecking_report')
    print(c)
    return b


@router.get('/latest')
def get_latest_data(
    file_name: str = Query(None, description='The wanted file. Use the keys from the "files" dict that you can get without this parameter')):
    return claimreview_scraper_connector.get_latest(file_name)


@router.get('/sample')
def get_random_samples(
    since: str = Query(None, description='Time filter, only get items published since the provided date. Format YYYY-MM-DD'),
    until: str = Query(None, description='Time filter, only get items published until the provided date. Format YYYY-MM-DD'),
    misinforming_domain: str = Query(None, description='The domain where misinformation is published, e.g., breitbart.com'),
    fact_checker_domain: str = Query(None, description='The domain of the factchecker, e.g., snopes.com'),
    exclude_misinfo_domain: list = Query(['twitter.com', 'wikipedia.org'], description='Whether to exclude fact-checked links to some domains. Default is `twitter.com` and `wikipedia.org` (`?exclude_misinfo_domain=twitter.com&exclude_misinfo_domain=wikipedia.org`). It will be discarded if `misinforming_domain` is set.'),
    exclude_homepage_url_misinfo: bool = Query(True, description='Whether to exclude fact-checked links that point to a homepage (no specific article, e.g. "https://www.senatemajority.com/"). Default is true.'),
    cursor: str = Query(None, description='The cursor to resume sampling')
    ):
    args = {
        'since': since,
        'until': until,
        'misinforming_domain': misinforming_domain,
        'fact_checker_domain': fact_checker_domain,
        'exclude_misinfo_domain': exclude_misinfo_domain,
        'exclude_homepage_url_misinfo': exclude_homepage_url_misinfo,
        'cursor': cursor
    }
    return claimreview_scraper_connector.get_sample(args)
