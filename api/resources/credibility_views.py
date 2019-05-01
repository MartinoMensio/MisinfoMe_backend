# this endpoint is for the visualisation and interrogation of the credibility scores and graph
from flask_restplus import Resource, marshal_with
import webargs
import marshmallow
import flask_restplus
from webargs.flaskparser import use_args, use_kwargs

from ..model import credibility_manager
from . import statuses

link = {
    'from': flask_restplus.fields.String,
    'to': flask_restplus.fields.String,
    'credibility': flask_restplus.fields.Float,
    'confidence': flask_restplus.fields.Float,
    'type': flask_restplus.fields.String
}

graph = {
    'nodes': flask_restplus.fields.Raw,
    'links': flask_restplus.fields.Nested(link),
}

class CredibilityGraph(Resource):
    @marshal_with(graph)
    def get(self):
        return credibility_manager.get_credibility_graph()

    @marshal_with(graph)
    def post(self):
        return credibility_manager.recreate_credibility_graph(), 201
