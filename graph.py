from caleydo_server.dataset_def import ADataSetProvider
import caleydo_graph.graph

class MongoGraph(caleydo_graph.graph.Graph):
  def __init__(self, entry, db):
    super(MongoGraph, self).__init__(entry['name'], 'mongodb', entry.get('id', None))
    self._entry = entry
    self._db = db
    from bson.objectid import ObjectId
    self._find_me = dict(_id=self._entry['_id'])
    self._find_data = dict(_id=ObjectId(self._entry['refid']))

    self._nodes = None
    self._edges = None

  @staticmethod
  def list(db):
    return [ MongoGraph(entry, db) for entry in db.graph.find()]

  @staticmethod
  def create(data, user, id, db):
    import datetime
    entry = dict(
      name=data['name'],
      description=data.get('description', ''),
      creator=user.name,
      nnodes=len(data['nodes']),
      nedges=len(data['edges']),
      ts=datetime.datetime.utcnow())
    if id is not None:
      entry['id'] = id

    data_entry = dict(
      nodes = data['nodes'],
      edges = data['edges']
    )
    data_id = db.graph_data.insert_one(data_entry).inserted_id

    entry['refid'] = str(data_id)
    db.graph.insert_one(entry)

    return MongoGraph(entry, db)

  def nodes(self, range=None):
    if self._nodes is None:
      from bson.objectid import ObjectId
      data = self._db.graph_data.findOne(self._find_data, {'nodes': 1})
      self._nodes = { n['id'] : caleydo_graph.graph.GraphNode(n['type'],n['id'], n.get('attrs',None)) for n in data['nodes'] }

    if range is None:
      return self._nodes
    return self._nodes[range.asslice()]

  @property
  def nnodes(self):
    return self._entry['nnodes']

  def edges(self, range = None):
    if self._edges is None:
      from bson.objectid import ObjectId
      data = self._db.graph_data.findOne(self._find_data, {'edges': 1})
      self._edges = [caleydo_graph.graph.GraphEdge(n['type'],n['source'], n['target'], n.get('attrs',None)) for n in data['edges']]

    if range is None:
      return self._edges
    return self._edges[range.asslice()]

  @property
  def num_edges(self):
    return self._entry['nedges']

  def to_description(self):
    r = super(MongoGraph, self).to_description()
    return r

  def add_node(self, data):
    self._db.graph.update(self._find_me, { '$inc': dict(nnodes=1) })
    self._db.graph_data.update(self._find_data, { '$push': dict(nodes=data) })
    return True

  def remove_node(self, id):
    self._db.graph.update(self._find_me, { '$inc': dict(nnodes=-1) })
    self._db.graph_data.update(self._find_data, { '$pull': dict(nodes=dict(id=id)) })
    return True

  def add_edge(self, data):
    self._db.graph.update(self._find_me, { '$inc': dict(nedges=1) })
    self._db.graph_data.update(self._find_data, { '$push': dict(edges=data) })
    return True

  def remove_edge(self, id):
    source,target = caleydo_graph.graph.GraphEdge.split_id(id)
    self._db.graph.update(self._find_me, { '$inc': dict(nedges=-1) })
    self._db.graph_data.update(self._find_data, { '$pull': dict(edges=dict(source=source,target=target)) })
    return True

  def remove(self):
    self._db.graph.remove(self._find_me)
    self._db.graph_data.remove(self._find_data)
    return True

class GraphProvider(ADataSetProvider):
  def __init__(self):
    import caleydo_server.config
    c = caleydo_server.config.view('caleydo_data_mongo')

    from pymongo import MongoClient
    self.client = MongoClient(c.host, c.port)
    self.db = self.client.graph

    self.entries = MongoGraph.list(self.db)

  def __len__(self):
    return len(self.entries)

  def __iter__(self):
    return iter(self.entries)

  def remove(self, entry):
    if isinstance(entry, MongoGraph) and entry in self.entries and entry.remove():
      self.entries.remove(entry)
      return True
    return False

  def upload(self, data, files, id=None):
    if not data.get('type','unknown') == 'graph':
      return None #can't handle
    from caleydo_server.security import manager
    m = manager()
    user = m.current_user

    parsed = caleydo_graph.graph.parse(data, files)

    if parsed is None:
      return None

    graph = MongoGraph.create(parsed, user, id, self.db)

    self.entries.append(graph)

    return graph

def create():
  return GraphProvider()
