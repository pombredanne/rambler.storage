from nose.tools import eq_, assert_raises
import os

from Rambler import field, coroutine
from Rambler.TestCase import TestCase

from models import Employee

class TestLifeCycleEvents(TestCase):
  componentName = 'Entity'
  test_options = {
    'storage.conf': {'default': 'InMemoryStorage'}
  }
  
  test_components = {
    'Employee': Employee
  }
  
  def setUp(self):
    super(TestLifeCycleEvents,self).setUp()
    # Create a dynamic class on the fly
    self.TestEntity = type('TestEntity', (self.Entity,), {'id': field(str)})
  
  @TestCase.coroutine
  def test_json_storage(self):
    self.test_options['storage.conf']['default'] = 'JSONStorage'
    self.test_commit()
    
  @TestCase.coroutine
  def test_commit(self):
    manager = yield self.Employee.create(name="El Guapo")
    # .. Q: is create now an op?
    uow = coroutine.context.rambler_storage_uow
  
    eq_(len(uow.objects()),     1)
    eq_(len(uow.get_new()),     1)
    eq_(len(uow.get_clean()),   0)
    eq_(len(uow.get_dirty()),   0)
    eq_(len(uow.get_removed()), 0)
  

    yield self.Employee.commit()

    # Commiting the transaction flushes the changes to the storage
    # the unit of work will keep track of the object now in the "clean"
    # state


    eq_(len(uow.objects()),     1)
    eq_(len(uow.get_new()),     0)
    eq_(len(uow.get_clean()),   1)
    eq_(len(uow.get_dirty()),   0)
    eq_(len(uow.get_removed()), 0)
  
    minion1 = yield self.Employee.create(name="El Hefe", manager=manager)
    
    minion1_manager = yield minion1.manager()
    
    eq_(minion1_manager, manager)
    
    subordinates = yield manager.subordinates()
    assert minion1 in subordinates
  
    eq_(len(uow.objects()),     2)
    eq_(len(uow.get_new()),     1)
    eq_(len(uow.get_clean()),   0)
    eq_(len(uow.get_dirty()),   1)
    eq_(len(uow.get_removed()), 0)

  
    yield self.Employee.commit()
    eq_(len(uow.objects()),     2)
    eq_(len(uow.get_new()),     0)
    eq_(len(uow.get_clean()),   2)
    eq_(len(uow.get_dirty()),   0)
    eq_(len(uow.get_removed()), 0)
  
    uow.clear()
    eq_(len(uow.objects()),     0)
    eq_(len(uow.get_new()),     0)
    eq_(len(uow.get_clean()),   0)
    eq_(len(uow.get_dirty()),   0)
    eq_(len(uow.get_removed()), 0)

