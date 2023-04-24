from fastapi import APIRouter, Path, Query

from ..model import jobs_manager
from ..model import credibility_manager
from ..model import entity_manager
from . import statuses

router = APIRouter()


@router.get("/home")
def get_frontend_v2_home():
    """Get the info to populate the homepage"""
    return entity_manager.get_frontend_v2_home()


@router.get("/home/most_popular_entries")
def get_frontend_v2_home_most_popular_entries():
    """Get the most searched profiles"""
    return entity_manager.get_most_popular_entries()


@router.post("/profiles")
def post_frontend_v2_profile_credibility(
    screen_name: str = Query(
        ..., description="The screen name of the profile to be analysed"
    ),
    until_id: str = Query(None, description="To continue previous analysis"),
    wait: bool = Query(False, description="Do you want to wait or to use job manager?"),
):
    """Get the credibility of a profile"""
    if not wait:
        return jobs_manager.create_task_for(
            credibility_manager.get_v2_profile_credibility, screen_name, until_id
        )
    else:
        return credibility_manager.get_v2_profile_credibility(screen_name, until_id)


@router.get("/profiles")
def get_frontend_v2_profile_credibility(
    screen_name: str = Query(
        ..., description="The screen name of the profile to be analysed"
    ),
    until_id: str = Query(None, description="To continue previous analysis"),
    wait: bool = Query(False, description="Do you want to wait or to use job manager?"),
):
    """Get the credibility of a profile"""
    if not wait:
        return jobs_manager.create_task_for(
            credibility_manager.get_v2_profile_credibility, screen_name, until_id
        )
    else:
        return credibility_manager.get_v2_profile_credibility(screen_name, until_id)


@router.get("/tweets/{tweet_id}")
def get_frontend_v2_tweet_credibility(
    tweet_id: int = Path(
        ..., description="The tweet is a identified by its ID, of type `int`"
    ),
    wait: bool = Query(False, description="Do you want to wait or to use job manager?"),
):
    """Get the credibility of a certain tweet"""
    if not wait:
        return jobs_manager.create_task_for(
            credibility_manager.get_v2_tweet_credibility, tweet_id
        )
    else:
        return credibility_manager.get_v2_tweet_credibility(tweet_id)
