from datetime import date
from typing import List
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel

from ..model import analysis_manager, jobs_manager

router = APIRouter()


class CountAnalysis(BaseModel):
    id: int
    screen_name: str
    profile_image_url: str
    tweets_cnt: int
    shared_urls_cnt: int
    verified_urls_cnt: int
    mixed_urls_cnt: int
    fake_urls_cnt: int
    unknown_urls_cnt: int
    score: int
    rebuttals: dict
    fake_urls: dict
    mixed_urls: dict
    verified_urls: dict
    updated: str
    cache: str


@router.get("/urls")
def get_url_analysis(url: str = Query(..., description="The URL to be analysed")):
    """
    Returns the analysis of the URL. GET is for cached results
    """
    # return analysis_manager.get_url_analysis(url)
    pass


@router.post("/urls")
def post_url_analysis(url: str = Query(..., description="The URL to be analysed")):
    """
    Returns the analysis of the URL. POST runs the analysis again
    """
    # return analysis_manager.get_url_analysis(url)
    pass


@router.get("/tweets")
def get_tweet_analysis(
    tweet_id: int = Path(..., description="The ID of the tweet to analyse")
):
    """
    Returns the analysis of the tweet. GET is for cached results
    """
    # return analysis_manager.get_tweet_analysis(tweet_id)
    pass


@router.post("/tweets")
def post_tweet_analysis(
    tweet_id: int = Path(..., description="The ID of the tweet to analyse")
):
    """
    Returns the analysis of the tweet. POST runs the analysis again
    """
    # return analysis_manager.get_tweet_analysis(tweet_id)
    pass


@router.get("/twitter_accounts")
def get_twitter_account_analysis(
    user_id: int = Query(None, description="The user ID to analyse"),
    screen_name: str = Query(None, description="The screen_name to analyse"),
    relation: str = Query(
        None,
        description="if set to `friends` will analyse the friends instead of the user itself",
    ),
    limit: int = Query(
        200,
        description="if `relation` is set to `friends`, this tells how many friends maximum to analyse",
    ),
    use_credibility: bool = Query(
        False,
        description="Wether to use the old model (false) or the new one based on credibility",
    ),
    wait: bool = Query(
        True,
        description="Do you want to be waiting, or get a work id that you can query later?",
    ),
):
    """
    Returns the analysis of the twitter account. GET is for cached results
    """
    allow_cached = True
    only_cached = True
    if wait:
        if relation == "friends":
            if screen_name:
                result = analysis_manager.analyse_friends_from_screen_name(
                    screen_name, limit, use_credibility=use_credibility
                )
            if user_id:
                result = analysis_manager.analyse_friends(
                    user_id, limit, use_credibility=use_credibility
                )
        elif user_id:
            result = analysis_manager.analyse_twitter_account(
                user_id,
                allow_cached=allow_cached,
                only_cached=only_cached,
                use_credibility=use_credibility,
            )
        elif screen_name:
            result = analysis_manager.analyse_twitter_account_from_screen_name(
                screen_name,
                allow_cached=allow_cached,
                only_cached=only_cached,
                use_credibility=use_credibility,
            )
        return CountAnalysis(result)
    else:
        if relation == "friends":
            raise HTTPException(
                status_code=400,
                detail="async job not supported with this combination of parameters. set wait=False",
            )
        elif user_id:
            raise HTTPException(
                status_code=400,
                detail="async job not supported with this combination of parameters. set wait=False",
            )
        elif screen_name:
            return jobs_manager.create_task_for(
                analysis_manager.analyse_twitter_account_from_screen_name,
                screen_name,
                allow_cached=allow_cached,
                only_cached=only_cached,
                use_credibility=use_credibility,
            )

    raise HTTPException(
        status_code=400, detail="Provide a user_id or screen_name as parameter"
    )


@router.post("/twitter_accounts")
def post_twitter_account_analysis(
    user_id: int = Query(None, description="The user ID to analyse"),
    screen_name: str = Query(None, description="The screen_name to analyse"),
    relation: str = Query(
        None,
        description="if set to `friends` will analyse the friends instead of the user itself",
    ),
    limit: int = Query(
        200,
        description="if `relation` is set to `friends`, this tells how many friends maximum to analyse",
    ),
    use_credibility: bool = Query(
        False,
        description="Wether to use the old model (false) or the new one based on credibility",
    ),
    wait: bool = Query(
        True,
        description="Do you want to be waiting, or get a work id that you can query later?",
    ),
):
    """
    Returns the analysis of the twitter account. POST is for running the analysis again
    """
    allow_cached = False
    only_cached = False
    if wait:
        if relation == "friends":
            if user_id:
                result = analysis_manager.analyse_friends(
                    user_id,
                    limit,
                    allow_cached=allow_cached,
                    only_cached=only_cached,
                    use_credibility=use_credibility,
                )
            elif screen_name:
                result = analysis_manager.analyse_friends_from_screen_name(
                    screen_name,
                    limit,
                    allow_cached=allow_cached,
                    only_cached=only_cached,
                    use_credibility=use_credibility,
                )
        elif user_id:
            result = analysis_manager.analyse_twitter_account(
                user_id,
                allow_cached=allow_cached,
                only_cached=only_cached,
                use_credibility=use_credibility,
            )
        elif screen_name:
            result = analysis_manager.analyse_twitter_account_from_screen_name(
                screen_name,
                allow_cached=allow_cached,
                only_cached=only_cached,
                use_credibility=use_credibility,
            )
        return CountAnalysis(result)
    else:
        if relation == "friends":
            raise HTTPException(
                status_code=400,
                detail="async job not supported with this combination of parameters. set wait=False",
            )
        elif user_id:
            raise HTTPException(
                status_code=400,
                detail="async job not supported with this combination of parameters. set wait=False",
            )
        elif screen_name:
            return jobs_manager.create_task_for(
                analysis_manager.analyse_twitter_account_from_screen_name,
                screen_name,
                allow_cached=allow_cached,
                only_cached=only_cached,
                use_credibility=use_credibility,
            )
    raise HTTPException(
        status_code=400, detail="Provide a user_id(s) or screen_name(s) as parameter"
    )


@router.get("/time_distribution_url")
def get_url_time_distribution_analysis(
    url: str = Query(None, description="The url to analyse temporally"),
    time_granularity: str = Query(
        "month",
        description="The time granularity wanted. Possible values are `year`, `month`, `week`, `day`",
    ),
):
    """
    Returns the time distribution of the url
    """
    if not url:
        raise HTTPException(status_code=400, detail="missing parameter url")
    return analysis_manager.analyse_time_distribution_url(url, time_granularity)


@router.get("/time_distribution_tweets")
def get_tweets_time_distribution_analysis(
    tweets_ids: List[int] = Query([], description="The IDs of the tweets to analyse"),
    time_granularity: str = Query(
        "month",
        description="The time granularity wanted. Possible values are `year`, `month`, `week`, `day`",
    ),
    mode: str = Query(
        "absolute",
        description="The mode for time. Possible values are `absolute`, `relative`",
    ),
    reference_date: date = Query(
        None, description="The reference date for relative mode"
    ),
):
    """
    Returns the time distribution of the tweets
    """
    return analysis_manager.analyse_time_distribution_tweets(
        tweets_ids, time_granularity, mode, reference_date
    )
