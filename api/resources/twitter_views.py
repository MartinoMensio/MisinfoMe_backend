# this endpoint is for the visualisation and interrogation of the credibility scores and graph
from fastapi import APIRouter

from ..external import twitter_connector
from .. import app

router = APIRouter()


@router.get("/tweets/{tweet_id}")
def get_tweet(tweet_id: int):
    """Get the origins used to create the assessments"""
    return twitter_connector.get_tweet(tweet_id)
