from fastapi import APIRouter, Query, Path

from ..model import entity_manager
from . import statuses

router = APIRouter()


# @router.get("/tweets")
# DEPRECATED AND NOT PUBLIC
def get_tweets(
    url: str = Query(..., description="Search the tweets containing this URL"),
    cached_only: bool = Query(
        False, description="Get only tweets that are already in the cache"
    ),
    from_date: str = Query(None, description="Select tweets after a certain date"),
):
    """
    Returns the tweets containing `url`
    """
    return entity_manager.get_tweets_containing_url(
        url, cached_only=cached_only, from_date=from_date
    )


@router.get("/users")
def get_twitter_account(
    screen_name: str = Query(..., description="The screen_name to look for")
):
    """
    Returns the twitter account matching `screen_name`
    """
    twitter_account = entity_manager.get_twitter_account_from_screen_name(screen_name)
    return twitter_account


# DEPRECATED
@router.get("/factchecking_organisations/{org_id}")
def get_factchecking_organisation(
    org_id: str = Path(
        ..., description="The id of the factchecking organisation to look for"
    )
):
    organisation = entity_manager.get_factchecking_organisation_from_id(org_id)
    if organisation:
        return organisation
    return {"error": "Factchecking organisation not found"}, 404


# DEPRECATED
@router.get("/factchecking_organisations")
def get_factchecking_organisations(
    belongs_to_ifcn: bool = None, valid_ifcn: bool = None, country: str = None
):
    return entity_manager.get_factchecking_organisations(
        belongs_to_ifcn=belongs_to_ifcn, valid_ifcn=valid_ifcn, country=country
    )


# Fact-checking reviews


# DEPRECATED
@router.get("/factchecking_reviews")
def get_factchecking_reviews(
    published_by_id: str = Query(
        None,
        description="Get the factchecking reviews published by a single organisation (identifier)",
    ),
    published_at_domain: str = Query(
        None, description="Get the factchecking reviews published on a certain domain"
    ),
    published_at_url: str = Query(
        None, description="Get the factchecking reviews published on a certain URL"
    ),
):
    if published_by_id:
        return entity_manager.get_factchecking_reviews_from_organisation_id(
            published_by_id
        )
    elif published_at_domain:
        return entity_manager.get_factchecking_reviews_at_domain(published_at_domain)
    elif published_at_url:
        return entity_manager.get_factchecking_reviews_at_url(published_at_url)
    else:
        return entity_manager.get_factchecking_reviews_by_factchecker()


# DEPRECATED
@router.get("/")
def get_data_stats():
    return entity_manager.get_data_stats()


# DEPRECATED
@router.get("/domains")
def get_domains():
    return entity_manager.get_domains()


# DEPRECATED
@router.get("/origins")
def get_origins():
    return entity_manager.get_origins()


# DEPRECATED
@router.get("/factcheckers_table")
def get_factcheckers_table():
    return entity_manager.get_factcheckers_table()
