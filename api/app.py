import os
import requests
from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
load_dotenv()

from . import resources
from .resources import static_resources



tags_metadata = [
    {"name": "entities", "description": "Basic entities stored in the service"},
    {"name": "analysis", "description": "Analysis of some entities. Deprecated version. Use credibility."},
    {"name": "credibility", "description": "Interfacing with the credibility component"},
    {"name": "stats", "description": "Some statistics"},
    {"name": "utils", "description": "Some utility functins"},
    {"name": "frontend-v2", "description": "The API for frontend v2 of MisinfoMe"},
    {"name": "jobs", "description": "Query the status of the jobs"},
    {"name": "data", "description": "Update data collection"},
    {"name": "data", "twitter": "Interfacing with the twitter connector"},
]
# app = FastAPI(title='MisinfoMe API', description='API for the MisinfoMe project', version='0.3.0', openapi_tags=tags_metadata, openapi_url='/misinfo/api/openapi.json', docs_url='/misinfo/api/docs', redoc_url='/misinfo/api/redoc',)
app = FastAPI(title='MisinfoMe API', description='API for the MisinfoMe project', version='0.3.0', openapi_tags=tags_metadata)


main_router = APIRouter()
resources.configure_endpoints(main_router)
static_resources.configure_static_resources(app)
app.include_router(main_router, prefix='/misinfo/api')
resources.configure_cors(app)
