import os
from fastapi import FastAPI, APIRouter
from starlette.applications import Starlette
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from starlette.responses import RedirectResponse

def config_angular_frontend(app: APIRouter | FastAPI, static_folder: str, url_prefix: str, name: str):
    # a new Starlette app that manages static files and 404 for angular (deep linking)
    frontend = Starlette()
    @frontend.middleware("http")
    async def fix_not_found(request, call_next):
        response = await call_next(request)
        if response.status_code == 404:
            return FileResponse(f'{static_folder}/index.html')
        return response
    @frontend.exception_handler(404)
    def not_found(request, exc):
        return FileResponse(f'{static_folder}/index.html')
    # mount the folder with the static files
    frontend.mount('/', StaticFiles(directory=static_folder))
    # and then mount to the main app
    app.mount(url_prefix, app=frontend, name=name)


def configure_static_resources(main_router: APIRouter | FastAPI):
    # frontend v1
    config_angular_frontend(main_router, 'app-v1', '/frontend-v1', 'static app v1')
    # frontend v2
    config_angular_frontend(main_router, 'app-v2', '/frontend-v2', 'static app v2')

    # root will go to the frontend v2
    @main_router.route('/')
    def redirect_home(request):
        return RedirectResponse(url='/frontend-v2/')
    
    # deep links to the frontend v1
    # /misinfo/credibility
    @main_router.get('/misinfo/credibility/tweets/{tweet_id}', include_in_schema=False)
    def redirect_tweet_credibility(tweet_id: str):
        return RedirectResponse(url=f'/frontend-v1/credibility/tweets/{tweet_id}')
    # /misinfo/credibility
    @main_router.get('/misinfo/credibility/sources', include_in_schema=False)
    def redirect_sources_credibility():
        return RedirectResponse(url=f'/frontend-v1/credibility/sources')
    @main_router.get('/misinfo/credibility/sources/{source}', include_in_schema=False)
    def redirect_source_credibility(source: str):
        return RedirectResponse(url=f'/frontend-v2/sources/{source}')
    
    # docs
    @main_router.get('/misinfo/api', include_in_schema=False)
    def redirect_home():
        return RedirectResponse(url='/docs')
