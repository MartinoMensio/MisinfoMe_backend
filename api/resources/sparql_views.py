from fastapi import APIRouter, Query
from rdflib import ConjunctiveGraph
from rdflib_endpoint import SparqlRouter

g = ConjunctiveGraph()

router = APIRouter()

sparql_router = SparqlRouter(
    graph=g,
    path="/",
    # Metadata used for the SPARQL service description and Swagger UI:
    title="SPARQL endpoint for RDFLib graph",
    description="A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python. \n[Source code](https://github.com/vemonet/rdflib-endpoint)",
    version="0.1.0",
    public_url='https://misinf.me/sparql',
    example_query="select distinct ?Concept where {[] a ?Concept} LIMIT 100"
)

router.include_router(sparql_router)

@router.get('/update')
def update():
    global g
    # TODO find a way to have triples from claimreview (~/KMi/coinform/claimskg-wrap)
    # from https://search.gesis.org/research_data/SDN-10.7802-2469?doi=10.7802/2469
    # wget https://access.gesis.org/sharing/2469/3961?download_purpose=scientific_research&agreed_user_terms=true
    # saved and extacted in this folder
    # recreate and load
    g = ConjunctiveGraph()
    g.parse('ClaimsKG(Aug2022).ttl', format='ttl')
    return 'ok'