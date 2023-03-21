# this endpoint is for the visualisation and interrogation of the credibility scores and graph
from typing import List
from fastapi import APIRouter, Body, HTTPException, Path, Query

from ..model import credibility_manager, jobs_manager
from .. import app

router = APIRouter()


@router.get('/origins')
def get_credibility_origins():
    """
    Get the origins used to create the assessments
    """
    return credibility_manager.get_credibility_origins()


@router.get('/factcheckers')
def get_factcheckers():
    """
    Get the factcheckers from IFCN
    """
    return credibility_manager.get_factcheckers()


@router.get('/sources')
def get_source_credibility(source: str = Query(..., description='The source to analyse')):
    """
    Get the credibility of a certain source
    """
    return credibility_manager.get_source_credibility(source)

@router.post('/sources')
def post_source_credibility(
    source: str = Query(..., description='The source to analyse'),
    callback_url: str = Query(None, description='The callback_url coming from the gateway. If absent, the call will be blocking')):
    """
    Get the credibility of a certain source
    """
    if callback_url:
        return jobs_manager.create_task_for(credibility_manager.get_source_credibility, source, callback_url=callback_url)
    else:
        return credibility_manager.get_source_credibility(source)


@router.get('/urls')
def get_url_credibility(url: str = Query(..., description='The URL to analyse')):
    """
    Get the credibility of a certain URL
    """
    return credibility_manager.get_url_credibility(url)

@router.post('/urls')
def post_url_credibility(
    url: str = Query(..., description='The URL to analyse'),
    callback_url: str = Query(None, description='The callback_url coming from the gateway. If absent, the call will be blocking')):
    """
    Get the credibility of a certain URL
    """
    if callback_url:
        return jobs_manager.create_task_for(credibility_manager.get_url_credibility, url, callback_url=callback_url)
    else:
        return credibility_manager.get_url_credibility(url)



@router.get('/tweets/{tweet_id}')
def get_tweet_credibility(
            tweet_id: int = Path(..., description='The tweet is a identified by its ID, of type `int`'),
            wait: bool = Query(True, description='Do you want to be waiting, or get a work id that you can query later?')):
    """Get the credibility of a certain tweet"""
    if not wait:
        return jobs_manager.create_task_for(credibility_manager.get_tweet_credibility_from_id, tweet_id)
    else:
        result = credibility_manager.get_tweet_credibility_from_id(tweet_id)
        if not result:
            raise HTTPException(status_code=404, detail="Tweet not found")
        return result


@router.post('/tweets/{tweet_id}')
def post_tweet_credibility(
            tweet_id: int = Path(..., description='The tweet is a identified by its ID, of type `int`'),
            callback_url: str = Query(None, description='The callback_url coming from the gateway. If absent, the call will be blocking')):
    """Endpoint for gateway"""
    if callback_url:
        return jobs_manager.create_task_for(credibility_manager.get_tweet_credibility_from_id, tweet_id, callback_url=callback_url)
    else:
        return credibility_manager.get_tweet_credibility_from_id(tweet_id)


@router.post('/tweets/batch')
def post_tweet_credibility_batch(
            tweets: List[dict] = Body(..., description='A list of tweets, each one being a dict with the keys `id` and `text`')):
    """Get the credibility of a batch of tweets"""
    return credibility_manager.get_tweet_credibility_from_dirty_tweet_batch(tweets)
    

@router.get('/users')
def get_user_credibility(
            screen_name: str = Query(..., description='The `screen_name` of the twitter profile to analyse'),
            wait: bool = Query(True, description='Do you want to be waiting, or get a work id that you can query later?')):
    """Get the credibility of a certain user"""
    if not wait:
        return jobs_manager.create_task_for(credibility_manager.get_user_credibility_from_screen_name, screen_name)
    else:
        result = credibility_manager.get_user_credibility_from_screen_name(screen_name)
        if not result:
            raise HTTPException(status_code=404, detail="Tweets not found")
        return result


@router.post('/users')
def post_user_credibility(
            screen_name: str = Query(..., description='The `screen_name` of the twitter profile to analyse'),
            callback_url: str = Query(None, description='A URL to be POSTed with the result of the job. If absent, the call will be blocking')):
    """Endpoint for gateway"""
    if callback_url:
        return jobs_manager.create_task_for(credibility_manager.get_user_credibility_from_screen_name, screen_name, callback_url=callback_url)
    else:
        return credibility_manager.get_user_credibility_from_screen_name(screen_name)


@router.get('/user-friends')
def get_user_friends_credibility(
            screen_name: str = Query(..., description='The `screen_name` of the twitter profile with the friends to get the cached analysis'),
            limit: int = Query(300, description='How many friends to retrieve, default 300')):
    """Get the credibility of a certain user"""
    result = credibility_manager.get_user_friends_credibility_from_screen_name(screen_name, limit)
    return result
