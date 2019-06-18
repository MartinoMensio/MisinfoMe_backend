from . import interface

from ...data import database

class DatasetResource(interface.IExternalSource):
    def update(self):
        domain_assessmments = database.get_domain_assessments()
        # TODO retrieve sources and populate the graph
