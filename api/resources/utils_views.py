from fastapi import APIRouter, Query


from ..model import utils_manager
from ..data import database
from ..model import jobs_manager
from ..external import twitter_connector, credibility_connector

router = APIRouter()


@router.get("/unshorten")
def unshorten_url(url: str = Query(..., description="The URL to unshorten")):
    unshortened = utils_manager.unshorten_url(url)

    return unshortened


@router.get("/time_published")
def get_url_published_time(
    url: str = Query(..., description="The URL to get the publishing time")
):
    result = utils_manager.get_url_published_time(url)

    return result


@router.get("/status")
def get_status():
    # test mongo
    try:
        mongo_ok = database.ping_db()["ok"]
        mongo_status = "ok" if mongo_ok == 1.0 else "error"
    except:
        mongo_status = "exception"
    # test redis
    try:
        redis_status = jobs_manager.health()
    except:
        redis_status = "exception"

    # test credibility
    credibility_res = credibility_connector.get_status()
    credibility_status = credibility_res["status"]
    # test twitter_connector
    twitter_res = twitter_connector.get_status()
    twitter_status = twitter_res["status"]

    print("mongo_status", mongo_status)
    print("redis_status", redis_status)
    print("credibility_status", credibility_status)
    print("twitter_status", twitter_status)

    if (
        mongo_status == "ok"
        and redis_status == "ok"
        and credibility_status == "ok"
        and twitter_status == "ok"
    ):
        status = "ok"
    else:
        status = "error"

    return {
        "status": status,
        "details": {
            "credibility": credibility_res,
            "twitter_connector": twitter_res,
            "mongo_status": mongo_status,
            "redis_status": redis_status,
        },
    }
