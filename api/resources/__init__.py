from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from . import (
    stats_views,
    analysis_views,
    utils_views,
    credibility_views,
    jobs_views,
    data_views,
    twitter_views,
)
from . import frontend_v2_views


def configure_endpoints(main_router: APIRouter):
    # endpoints for the analyses
    main_router.include_router(
        analysis_views.router, prefix="/analysis", tags=["analysis"]
    )

    # endpoints for the credibility graph
    main_router.include_router(
        credibility_views.router, prefix="/credibility", tags=["credibility"]
    )

    # endpoints for the stats
    main_router.include_router(stats_views.router, prefix="/stats", tags=["stats"])

    # endpoints for utils
    main_router.include_router(utils_views.router, prefix="/utils", tags=["utils"])

    # endpoints for the new frontend
    main_router.include_router(
        frontend_v2_views.router, prefix="/frontend/v2", tags=["frontend-v2"]
    )

    # endpoints for the jobs
    main_router.include_router(jobs_views.router, prefix="/jobs", tags=["jobs"])

    # endpoints for data automatic update
    main_router.include_router(data_views.router, prefix="/data", tags=["data"])

    # twitter api
    main_router.include_router(
        twitter_views.router, prefix="/twitter", tags=["twitter"]
    )


def configure_cors(app):
    origins = [
        "*",  # allow all origins
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
