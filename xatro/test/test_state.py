from twisted.trial.unittest import TestCase


from xatro.state import State
from xatro.event import Created, Destroyed, AttrSet, ItemAdded, ItemRemoved
from xatro.event import AttrDel



class StateTest(TestCase):


    def test_Created(self):
        """
        When an object is created, add it to the state dict.
        """
        state = State()
        state.eventReceived(Created('foo'))
        self.assertEqual(state.state['foo'], {'id': 'foo'})


    def test_Destroyed(self):
        """
        When an object is destroyed, remove it from the state dict.
        """
        state = State()
        state.eventReceived(Created('foo'))
        state.eventReceived(Destroyed('foo'))
        self.assertEqual(state.state, {})


    def test_AttrSet(self):
        """
        When an attribute is set, it should be set in the state dict.
        """
        state = State()
        state.eventReceived(Created('foo'))
        state.eventReceived(AttrSet('foo', 'theattr', 4))
        self.assertEqual(state.state['foo']['theattr'], 4)


    def test_AttrDel(self):
        """
        When an attribute is deleted, it should be deleted in the state dict.
        """
        state = State()
        state.eventReceived(Created('foo'))
        state.eventReceived(AttrSet('foo', 'name', 10))
        state.eventReceived(AttrDel('foo', 'name'))
        self.assertNotIn('name', state.state['foo'])


    def test_ItemAdded(self):
        """
        When an item is added, it should be added to a list attribute on the
        object.
        """
        state = State()
        state.eventReceived(Created('foo'))
        state.eventReceived(ItemAdded('foo', 'thelist', 10))
        self.assertEqual(state.state['foo']['thelist'], [10])

        state.eventReceived(ItemAdded('foo', 'thelist', 20))
        self.assertEqual(state.state['foo']['thelist'], [10, 20])


    def test_ItemRemoved(self):
        """
        When an item is removed, it should be removed from the list attribute
        on the object.
        """
        state = State()
        state.eventReceived(Created('foo'))
        state.eventReceived(ItemAdded('foo', 'thelist', 10))
        state.eventReceived(ItemRemoved('foo', 'thelist', 10))
        self.assertEqual(state.state['foo']['thelist'], [])


    def test_unknownEvents(self):
        """
        Unknown events should fail silently
        """
        state = State()
        state.eventReceived('foo')
        class Foo(object): pass
        state.eventReceived(Foo())