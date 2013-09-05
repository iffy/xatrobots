from twisted.trial.unittest import TestCase
from twisted.internet import defer

from mock import MagicMock

from xatro.world import World
from xatro.event import Created, Destroyed, AttrSet, ItemAdded, ItemRemoved


class WorldTest(TestCase):


    def test_init(self):
        """
        A world has an event receiver that will be supplied with all the
        events.
        """
        called = []
        world = World(called.append)
        world.emit('foo')
        self.assertEqual(called, ['foo'], "Should receive the event")


    def test_create(self):
        """
        You can create objects.
        """
        ev = MagicMock()

        world = World(ev)
        obj = world.create('foo')
        self.assertIn('id', obj)
        self.assertEqual(obj['kind'], 'foo')

        self.assertEqual(obj, world.objects[obj['id']], "Should be in the "
                         "objects list")
        ev.assert_any_call(Created(obj['id']))
        ev.assert_any_call(AttrSet(obj['id'], 'kind', 'foo'))


    def test_create_uniqueId(self):
        """
        The id of an object should be unique
        """
        world = World(MagicMock())
        o1 = world.create('foo')
        o2 = world.create('bar')
        self.assertNotEqual(o1['id'], o2['id'])


    def test_get(self):
        """
        You can get objects.
        """
        world = World(MagicMock())
        obj = world.create('foo')
        obj2 = world.get(obj['id'])
        self.assertEqual(obj, obj2)


    def test_setAttr(self):
        """
        You can set the value of an attribute.
        """
        ev = MagicMock()
        world = World(ev)
        obj = world.create('foo')

        ev.reset_mock()
        world.setAttr(obj['id'], 'foo', 'bar')

        ev.assert_any_call(AttrSet(obj['id'], 'foo', 'bar'))
        obj = world.get(obj['id'])
        self.assertEqual(obj['foo'], 'bar')


    def test_destroy(self):
        """
        You can destroy an object
        """
        ev = MagicMock()
        world = World(ev)
        obj = world.create('foo')

        ev.reset_mock()
        world.destroy(obj['id'])

        ev.assert_any_call(Destroyed(obj['id']))
        self.assertNotIn(obj['id'], world.objects)


    def test_addItem(self):
        """
        You can add items to a list
        """
        ev = MagicMock()
        world = World(ev)
        obj = world.create('foo')

        ev.reset_mock()
        world.addItem(obj['id'], 'foo', 'bar')

        ev.assert_any_call(ItemAdded(obj['id'], 'foo', 'bar'))

        obj = world.get(obj['id'])
        self.assertEqual(obj['foo'], ['bar'])


    def test_removeItem(self):
        """
        You can remove items from a list
        """
        ev = MagicMock()
        world = World(ev)
        obj = world.create('foo')
        world.addItem(obj['id'], 'foo', 'bar')
        
        ev.reset_mock()
        world.removeItem(obj['id'], 'foo', 'bar')

        ev.assert_any_call(ItemRemoved(obj['id'], 'foo', 'bar'))
        self.assertEqual(world.get(obj['id'])['foo'], [])


    def test_onBecome(self):
        """
        You can get a Deferred which will fire when an attribute becomes a
        particular value.
        """
        world = World(MagicMock())

        obj = world.create('foo')
        d = world.onBecome(obj['id'], 'hey', 3)
        self.assertFalse(d.called)

        world.setAttr(obj['id'], 'hey', 3)
        self.assertEqual(self.successResultOf(d), 3)

        # make sure it isn't called again
        world.setAttr(obj['id'], 'hey', 2)
        world.setAttr(obj['id'], 'hey', 3)


    def test_onBecome_cancel(self):
        """
        You can cancel the deferred returned by onBecome
        """
        world = World(MagicMock())

        obj = world.create('foo')
        d = world.onBecome(obj['id'], 'hey', 3)
        d.cancel()

        world.setAttr(obj['id'], 'hey', 3)

        self.assertFailure(d, defer.CancelledError)


    def test_onChange(self):
        """
        You can get a Deferred which will fire when an attribute changes
        """
        world = World(MagicMock())

        obj = world.create('foo')
        d = world.onChange(obj['id'], 'hey')
        self.assertFalse(d.called)

        world.setAttr(obj['id'], 'ho', 8)
        self.assertFalse(d.called)

        world.setAttr(obj['id'], 'hey', 3)
        self.assertEqual(self.successResultOf(d), 3)

        # make sure it isn't called again
        world.setAttr(obj['id'], 'hey', 2)


    def test_onChange_cancel(self):
        """
        You can cancel the deferred returned by onChange
        """
        world = World(MagicMock())

        obj = world.create('foo')
        d = world.onChange(obj['id'], 'hey')
        d.cancel()

        world.setAttr(obj['id'], 'hey', 3)

        self.assertFailure(d, defer.CancelledError)


    def test_emit_Exception(self):
        """
        Exceptions caused by event receivers should not prevent other event
        receivers from receiving the events.
        """
        ev1 = MagicMock()
        ev1.side_effect = Exception()
        world = World(ev1)

        ev2 = MagicMock()
        ev2.side_effect = Exception()
        world.subscribeTo('1234', ev2)

        ev3 = MagicMock()
        world.subscribeTo('1234', ev3)

        world.emit('hey', '1234')
        ev1.assert_called_once_with('hey')
        ev2.assert_called_once_with('hey')
        ev3.assert_called_once_with('hey')


    def test_emitterFor(self):
        """
        You can get a function that takes a single argument and emits events
        for a particular object.
        """
        ev1 = MagicMock()
        world = World(ev1)

        ev2 = MagicMock()
        world.subscribeTo('1234', ev2)

        emitter = world.emitterFor('1234')
        emitter('foo')

        ev1.assert_called_once_with('foo')
        ev2.assert_called_once_with('foo')


    def test_emitterFor_same(self):
        """
        You should get the same function each time you ask for an emitter for
        the same object.
        """
        world = World(MagicMock())
        self.assertEqual(world.emitterFor('foo'), world.emitterFor('foo'))


    def test_subscribeTo(self):
        """
        You can subscribe to the events that are emitted by a particular object.
        """
        ev = MagicMock()
        world = World(ev)

        obj = world.create('foo')
        called = []
        world.subscribeTo(obj['id'], called.append)
        ev.reset_mock()

        world.emit('event', obj['id'])
        self.assertEqual(called, ['event'])
        ev.assert_called_once_with('event')
        ev.reset_mock()

        world.unsubscribeFrom(obj['id'], called.append)
        world.emit('event', obj['id'])
        self.assertEqual(called, ['event'], "Should not have changed")
        ev.assert_called_once_with('event')


    def test_receiveFor(self):
        """
        You can subscribe to the events that are received by a particular
        object.
        """
        ev = MagicMock()
        world = World(ev)

        obj = world.create('foo')
        called = []
        world.receiveFor(obj['id'], called.append)
        world.eventReceived('event', obj['id'])

        self.assertEqual(called, ['event'])
        called.pop()

        world.stopReceivingFor(obj['id'], called.append)
        world.eventReceived('foo', obj['id'])

        self.assertEqual(called, [], "Should not receive")


    def test_receiverFor(self):
        """
        You can get a function that will call eventReceived for a given object.
        """
        world = World(MagicMock())

        obj = world.create('foo')
        called = []
        world.receiveFor(obj['id'], called.append)

        receiver = world.receiverFor(obj['id'])
        receiver('hey')
        self.assertEqual(called, ['hey'])


    def test_receiverFor_same(self):
        """
        You should get the same function each time you ask for a receiver for
        the same object.
        """
        world = World(MagicMock())
        self.assertEqual(world.receiverFor('foo'), world.receiverFor('foo'))


    def test_selfReceiving(self):
        """
        All things should receive their own events by default.
        """
        world = World(MagicMock())
        thing = world.create('foo')

        called = []
        world.receiveFor(thing['id'], called.append)

        world.emit('foo', thing['id'])
        self.assertEqual(called, ['foo'], "Things should receive their own "
                         "emissions")


    def test_disable_selfReceiving(self):
        """
        You can disable self-receipt by creating things with a special arg.
        """
        world = World(MagicMock())
        thing = world.create('foo', receive_emissions=False)

        called = []
        world.receiveFor(thing['id'], called.append)

        world.emit('foo', thing['id'])
        self.assertEqual(called, [], "Should not receive because it was "
                         "disabled on creation.")











