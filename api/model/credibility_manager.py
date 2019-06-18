from ..data import database
from ..credibility import graph

def get_credibility_graph():
    """Returns the graph of credibility, as set of links and nodes"""
    nodes = database.credibility_get_nodes()
    nodes = {n['_id']: n for n in nodes}
    links = []

    for n_id, n in nodes.items():
        outgoing_links = database.credibility_get_outgoing_links_from_node_id(n_id)
        outgoing_links = [e for e in outgoing_links]
        links.extend(outgoing_links)

    return {
        'nodes': nodes,
        'links': links
    }

def recreate_credibility_graph():
    database.credibility_reset()

    graph.update()

    # create the head and default nodes
    database.credibility_add_node('head', {'name': 'The head of credibility. Customisable'})
    database.credibility_add_node('default', {'name': 'The default credibility'})
    database.credibility_add_link('head', 'default', {'credibility': 1.0, 'confidence': 1.0})
    # load from the dataset_resources
    dataset_graph = database.get_dataset_graph()
    for n_key, n in dataset_graph['nodes'].items():
        database.credibility_add_node(n_key, n)

    for l in dataset_graph['links']:
        database.credibility_add_link(l['from'], l['to'], l)

    """
    database.credibility_add_node('IFCN', {'name': 'International Fact Checking Network'})
    for fact_checker in database.get_fact_checkers():
        database.credibility_add_node(fact_checker['_id'], fact_checker)
        # TODO compute credibility and confidence based on the skills
        database.credibility_add_link('IFCN', fact_checker['_id'], {'credibility': 1.0, 'confidence': 1.0})
    """

    # What can you believe in by default?
    database.credibility_add_link('default', 'ifcncodeofprinciples.poynter.org', {'credibility': 1.0, 'confidence': 1.0})

    return get_credibility_graph()