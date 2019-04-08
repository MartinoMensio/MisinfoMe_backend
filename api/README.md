# API

The structure is the following:

- resources: contains classes to map REST requests and endpoints to model functions
- model: is the entrypoint containing all the functions that can be called externally
    - entity_manager: manages the entities
    - analysis_manager: manages the analysis also using the entity manager
- data: contains specific methods
    - twitter: interfacing with twitter
    - database: interfaces with the mongo database
    - unshortener: manages URL unshortening
    - utils: util functions
- evaluation: contains the methods for computing the credibility / counts / scores
    - TODO