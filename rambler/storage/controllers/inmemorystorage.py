import itertools

from collections import defaultdict
from Rambler import component
from Rambler.LRU import LRU

class InMemoryStorage(component('Operation')):
  block = None
  is_concurrent=True
  
  @classmethod
  def assembled(cls):
    cls.rebase()
    cls.storage_by_class = defaultdict(lambda: LRU(10))
    
  @classmethod
  def will_disassemble(cls):
    cls.storage_by_class.clear()
  
  @classmethod
  def create(cls, obj):
    """Copy attributes to the in memory storage"""
    
    operation = cls()
    operation.records = [obj]
    
    def create_obj(records):
      operation.record = {}
      obj.encode_with(operation)
      InMemoryStorage.storage_by_class[type(obj)][obj.primary_key] = operation.record
      obj._is_new = False
      return obj
      
    operation.block = create_obj
    
    return operation
    
  update = create
  
  @classmethod
  def find(cls, model, retrieval, order=None, limit=None, conditions=None, **kw):

    conditions = conditions or kw

    op = cls()
    objects = cls.storage_by_class[model]
    
    if retrieval not in ('first', 'all'):
      op.records = model(**objects[retrieval])
      return op
      
    def matches(record):
      for key,val in conditions.items():
        if record[key] != val:
          return False
      return True

    op.records = filter(matches, objects.values())
    if retrieval == 'first':
      def first(records):
        if records:
          return model(**records[0])
      op.block = first
    else:
      def lazy_map_all(records):
        return map(lambda r: model(**r), records)
      op.block = lazy_map_all
     
    return op   
    #attributes = cls.storage_by_class[model][retrieval]
    #return model(**attributes)


  @classmethod
  def count(cls, model, column_name='*', conditions=None):
    op = cls.find(model, "all",  conditions=conditions)
    op.block = len
    return op
    
  @classmethod
  def maximum(cls, model, column_name, conditions=None):
    op = cls.find(model, "all", order=column_name, limit=1, conditions=conditions)
    def first_column(records):
      if len(records):
        return records[0][column_name]
    
    op.block = first_column
    return op
    

  def __init__(self):
    super(InMemoryStorage, self).__init__()
  
  def main(self):
    pass

  
  def encode_object_for(self, object, key):
    '''Copy keys that an object wishes serialized to an in memory dictionary'''
    self.record[key] = object
  
  @property
  def result(self):
    if self.block:
      return self.block(self.records)
    else:
      return self.records