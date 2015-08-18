from caleydo_server.util import jsonify
from py2neo import Graph, Node, Relationship
from caleydo_server.dataset_def import ADataSetProvider

class Graph(object):
  def __init__(self):
    self.type = 'graph'

    pass

  def to_description(self):
    return dict(type='graph')

  def to_idtype_descriptions(self):
    return []

  def asnumpy(self, range=None):
    pass

  def asjson(self, range=None):
    pass

class GraphProvider(ADataSetProvider):
  def __init__(self):
    pass

def create():
  return GraphProvider()

def add_graph_handler(app, dataset_getter):
  @app.route('/graph/<int:datasetid>')
  def list_graphs(datasetid):
    d = dataset_getter(datasetid,'graph')
    return []

  @app.route('/graph/<int:datasetid>/nodes')
  def list_nodes(datasetid):
    d = dataset_getter(datasetid,'graph')
    return []

  @app.route('/graph/<int:datasetid>/edges')
  def list_edges(datasetid):
    d = dataset_getter(datasetid,'graph')
    return []

