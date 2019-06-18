# Backend

This is a REST service that acts as backend.

## Structure of code

The folders are organised in the following way:

- api: contains the implementation of the REST service
    - resources: REST endpoints / views
    - model: the high level model endpoints. It is the interface to the computation and data management
    - credibility: the core of computation of what is credible
        - graph: building and traversing the graph of credibility
        - sources: where the data comes from (API / datasets)
- app (unversioned): contains the transpiled frontend (look at https://github.com/MartinoMensio/MisinfoMe_frontend)
- examples: contains some json examples of the responses provided
- test: some tests

## Structure of the API

To all the path, they are relative to `/misinfo/api`

- `/`: Swagger automatic documentation
- `/entities`: See the entities contained in the backend
- `/utils`: Utility API
- `/analysis`: Old endpoints for the analysis
- `/credibility`: New endpoints for credibility graph

## Installation

You can use the Dockerfile, or install this by creating a venv and installing the requirements. Use python3
