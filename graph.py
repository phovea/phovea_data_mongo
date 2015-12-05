from caleydo_server.dataset_def import ADataSetProvider
import caleydo_graph.graph

class MongoGraph(caleydo_graph.graph.Graph):
  def __init__(self, entry, db):
    super(MongoGraph, self).__init__(entry['name'], 'mongodb', entry.get('id', None), entry.get('attrs',None))
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
    #if 'clone_from' in data:
    #  #clone from an existing graph
    #  from bson.objectid import ObjectId
    #  other_desc = db.graph.find_one(dict(_id=data['clone_from']))
    #  other_data = db.graph_data.find_one(dict(_id=ObjectId(other_desc['refid'])))
    #else
    #  other_desc = dict()
    #  other_data = dict()

    import datetime
    entry = dict(
      name=data['name'],
      description=data.get('description', ''),
      creator='unknown' if user.is_anonymous else user.name,
      nnodes=len(data['nodes']),
      nedges=len(data['edges']),
      attrs=data.get('attrs',{}),
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
      data = self._db.graph_data.find_one(self._find_data, {'nodes': 1})
      self._nodes = [ caleydo_graph.graph.GraphNode(n['type'],n['id'], n.get('attrs',None)) for n in data['nodes'] ]

    if range is None:
      return self._nodes
    return self._nodes[range.asslice()]

  @property
  def nnodes(self):
    return self._entry['nnodes']

  def edges(self, range = None):
    if self._edges is None:
      from bson.objectid import ObjectId
      data = self._db.graph_data.find_one(self._find_data, {'edges': 1})
      self._edges = [ caleydo_graph.graph.GraphEdge(n['type'],n['id'], n['source'], n['target'], n.get('attrs',None)) for n in data['edges'] ]

    if range is None:
      return self._edges
    return self._edges[range.asslice()]

  @property
  def nedges(self):
    return self._entry['nedges']

  def to_description(self):
    r = super(MongoGraph, self).to_description()
    return r

  def add_node(self, data):
    self._db.graph.update(self._find_me, { '$inc': dict(nnodes=1) })
    self._db.graph_data.update(self._find_data, { '$push': dict(nodes=data) })
    self._entry['nnodes'] += 1
    if self._nodes:
      self._nodes.append(caleydo_graph.graph.GraphNode(data['type'],data['id'], data.get('attrs',None)))
    return True

  def remove_node(self, id):
    if self._nodes:
      n = self.get_node(id)
      self._nodes.remove(n)
    self._entry['nnodes'] -= 1
    #remove node and all associated edges
    x = self._db.graph_data.update(self._find_data, {'$pull': dict(nodes=dict(id=id))}, multi=False)

    y = self._db.graph_data.update(self._find_data, {'$pull': dict(edges={'$or': [dict(source=id), dict(target=id)]})}, multi=True)


    if self._edges:
      self._edges = [e for e in self._edges if e.source != id and e.target != id]
      self._entry['nedges'] = len(self._edges)
    else:
      #use a query to compute the length
      self._entry['nedges'] = len(self._db.graph_data.find_one(self._find_data, {'edges': 1})['edges'])
    self._db.graph.update(self._find_me, { '$inc': dict(nnodes=-1) , '$set': dict(nedges=self._entry['nedges'])})

    return True

  def get_node(self, id):
    for n in self.nodes():
      if n.id == id:
        return n
    return None

  def get_edge(self, id):
    for n in self.edges():
      if n.id == id:
        return n
    return None

  def clear(self):
    self._db.graph.update(self._find_me, { '$set': dict(nnodes=0,nedges=0) })
    self._db.graph_data.update(self._find_data, { '$set': dict(nodes=[],edges=[]) })
    self._nodes = None
    self._edges = None
    self._entry['nnodes'] = 0
    self._entry['nedges'] = 0
    return True


  def add_edge(self, data):
    self._db.graph.update(self._find_me, { '$inc': dict(nedges=1) })
    self._db.graph_data.update(self._find_data, { '$push': dict(edges=data) })
    self._entry['nedges'] += 1
    if self._edges:
      self._edges.append(caleydo_graph.graph.GraphEdge(data['type'],data['id'],data['source'], data['target'], data.get('attrs',None)))
    return True

  def remove_edge(self, id):
    if self._edges:
      n = self.get_edge(id)
      self._edges.remove(n)
    self._entry['nedges'] -= 1
    self._db.graph.update(self._find_me, { '$inc': dict(nedges=-1) })
    self._db.graph_data.update(self._find_data, { '$pull': dict(edges=dict(id=id)) })
    return True

  def remove(self):
    self._db.graph.remove(self._find_me)
    self._db.graph_data.remove(self._find_data)
    self._nodes = None
    self._edges = None
    self._entry['nnodes'] = 0
    self._entry['nedges'] = 0
    return True

def _generate_id(basename):
  import caleydo_server.util
  return caleydo_server.util.fix_id(basename + ' ' + caleydo_server.util.random_id(5))

class GraphProvider(ADataSetProvider):
  def __init__(self):
    import caleydo_server.config
    c = caleydo_server.config.view('caleydo_data_mongo')

    from pymongo import MongoClient
    self.client = MongoClient(c.host, c.port)
    self.db = self.client.graph

  @property
  def entries(self):
    return MongoGraph.list(self.db)

  def __len__(self):
    return len(self.entries)

  def __iter__(self):
    return iter(self.entries)

  def remove(self, entry):
    if isinstance(entry, MongoGraph) and entry.remove():
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

    if id is None:
      id = _generate_id(parsed.get('name',''))

    graph = MongoGraph.create(parsed, user, id, self.db)

    return graph

def create():
  return GraphProvider()
