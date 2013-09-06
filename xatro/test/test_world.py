from twisted.trial.unittest import TestCase
from twisted.internet import defer

from mock import MagicMock

from xatro.world import World
from xatro.event import Created, Destroyed, AttrSet, ItemAdded, ItemRemoved
from xatro.event import ActionPerformed, AttrDel



class WorldTest(TestCase):

    timeout = 1

    def test_emit(self):
        """
        All emissions are sent to my event_receiver
        """
        ev = MagicMock()
        world = World(ev)
        world.emit('something', 'foo')
        ev.assert_called_once_with('something')


    def test_auth(self):
        """
        World can have an authenticator.
        """
        world = World(None, None, 'auth')
        self.assertEqual(world.auth, 'auth')


    def test_execute(self):
        """
        Asking the world to execute a command will ask the (game) engine to
        execute the command.
        """
        engine = MagicMock()
        engine.execute.return_value = 'response'
        
        world = World(MagicMock(), engine)
        world.emit = MagicMock()

        action = MagicMock()
        action.emitters.return_value = ['I did it']

        r = world.execute(action)
        
        engine.execute.assert_called_once_with(world, action)
        self.assertEqual(self.successResultOf(r), 'response',
                         "Should return the result of execution")
        world.emit.assert_called_once_with(ActionPerformed(action), 'I did it')


    def test_execute_Deferred(self):
        """
        If a command returns a successful deferred, wait to emit.
        """
        engine = MagicMock()
        d = defer.Deferred()
        engine.execute.return_value = d
        
        world = World(MagicMock(), engine)
        world.emit = MagicMock()

        action = MagicMock()
        action.emitters.return_value = ['I did it']

        r = world.execute(action)
        self.assertEqual(r, d, "Should return the result of the execution")
        
        engine.execute.assert_called_once_with(world, action)
        self.assertEqual(world.emit.call_count, 0, "Should not have emitted "
                         "the ActionPerformed event yet, because it hasn't "
                         "finished")
        d.callback('foo')
        self.assertEqual(self.successResultOf(r), 'foo',
                         "Should return the result of execution")
        world.emit.assert_called_once_with(ActionPerformed(action), 'I did it')


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


    def test_delAttr(self):
        """
        You can delete attributes.
        """
        ev = MagicMock()
        world = World(ev)
        obj = world.create('foo')
        world.setAttr(obj['id'], 'foo', 'bar')
        ev.reset_mock()

        world.delAttr(obj['id'], 'foo')
        ev.assert_any_call(AttrDel(obj['id'], 'foo'))
        self.assertNotIn('foo', world.get(obj['id']))


    def test_destroy(self):
        """
        You can destroy an object, and be notified about it.
        """
        ev = MagicMock()
        world = World(ev)
        obj = world.create('foo')

        ev.reset_mock()
        called = []
        world.receiveFor(obj['id'], called.append)

        world.destroy(obj['id'])

        ev.assert_any_call(Destroyed(obj['id']))
        self.assertEqual(called, [Destroyed(obj['id'])], "Should notify things"
                         " receiving events for the object")
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


    def test_onNextChange(self):
        """
        You can get a Deferred which will fire when an attribute changes
        """
        world = World(MagicMock())

        obj = world.create('foo')
        d = world.onNextChange(obj['id'], 'hey')
        self.assertFalse(d.called)

        world.setAttr(obj['id'], 'ho', 8)
        self.assertFalse(d.called)

        world.setAttr(obj['id'], 'hey', 3)
        self.assertEqual(self.successResultOf(d), 3)

        # make sure it isn't called again
        world.setAttr(obj['id'], 'hey', 2)


    def test_onNextChange_cancel(self):
        """
        You can cancel the deferred returned by onNextChange
        """
        world = World(MagicMock())

        obj = world.create('foo')
        d = world.onNextChange(obj['id'], 'hey')
        d.cancel()

        world.setAttr(obj['id'], 'hey', 3)

        self.assertFailure(d, defer.CancelledError)


    def test_onEvent(self):
        """
        You can be notified when a certain event happens.
        """
        world = World(MagicMock())

        obj = world.create('foo')['id']

        d = world.onEvent(obj, 'event')
        self.assertEqual(d.called, False)

        world.emit('event', obj)
        self.assertEqual(self.successResultOf(d), 'event')

        # shouldn't die calling again
        world.emit('event', obj)


    def test_onEvent_cancel(self):
        """
        You can cancel the deferred returned by onEvent
        """
        world = World(MagicMock())

        obj = world.create('foo')

        d = world.onEvent(obj['id'], 'hey')
        d.cancel()

        world.emit('hey', obj['id'])

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


    def test_destroy_disableSubscribers(self):
        """
        When an object is destroyed, things subscribed to its events will
        no longer receive events.
        """
        world = World(MagicMock())
        thing = world.create('foo')

        received = []
        world.receiveFor(thing['id'], received.append)

        emitted = []
        world.subscribeTo(thing['id'], emitted.append)

        receiver = world.receiverFor(thing['id'])
        emitter = world.emitterFor(thing['id'])

        world.destroy(thing['id'])
        received.pop()
        emitted.pop()

        receiver('foo')
        self.assertEqual(received, [])
        self.assertEqual(emitted, [])

        emitter('foo')
        self.assertEqual(received, [])
        self.assertEqual(emitted, [])


    def test_envelope(self):
        """
        You can read/write on the envelope of objects.
        """
        world = World(MagicMock())
        obj = MagicMock()
        env = world.envelope(obj)
        self.assertTrue(isinstance(env, dict))
        env['foo'] = 'bar'


    def test_envelope_ids(self):
        """
        You can read/write on the envelope of things in the world (using their
        id).
        """
        world = World(MagicMock())
        obj_id = world.create('foo')['id']
        env = world.envelope(obj_id)
        self.assertTrue(isinstance(env, dict))
        env['foo'] = 'bar'

        # destruction should destroy the envelope too
        world.destroy(obj_id)
        self.assertRaises(KeyError, world.envelope, obj_id)


    def test_emit_oneEventAtATime(self):
        """
        Only one event should be emitted at a time.  If an event emission
        causes another event to be emitted, it should be appended to a queue
        and be emitted after the current event is finished.
        """
        world = World(MagicMock())
        obj1 = world.create('foo')['id']
        obj2 = world.create('foo')['id']
        obj3 = world.create('foo')['id']

        obj1_received = []
        world.receiveFor(obj1, obj1_received.append)
        
        obj2_received = []
        world.receiveFor(obj2, obj2_received.append)

        obj3_received = []
        world.receiveFor(obj3, obj3_received.append)

        # obj1 will emit to
        #   obj2 and obj3
        world.subscribeTo(obj1, world.receiverFor(obj2))
        world.subscribeTo(obj1, world.receiverFor(obj3))

        # obj2 will emit to
        #   obj1 and obj3
        world.subscribeTo(obj2, world.receiverFor(obj1))
        world.subscribeTo(obj2, world.receiverFor(obj3))


        #       1_
        #      /|\
        #     /   \
        #   |/_   _\|
        #   3 <---- 2

        # obj2 will emit "obj2" every time he receives an event
        def noisy(_):
            world.emit('obj2', obj2)
        world.receiveFor(obj2, noisy)

        # If things are working properly, then obj3 will receive
        # the 'obj2' emissions AFTER it receives the event from obj1
        world.emit('obj1', obj1)
        self.assertEqual(obj1_received, ['obj1', 'obj2'],
                         "obj1 should receive obj1 from self, then obj2")
        self.assertEqual(obj2_received, ['obj1', 'obj2'],
                         "obj2 should receive obj1, then obj2 from self")
        self.assertEqual(obj3_received, ['obj1', 'obj2'],
                         "obj3 should receiver obj1 first, then obj2")


    def test_emit_receiveOnce(self):
        """
        Events should only be received by each object once.
        """
        world = World(MagicMock())
        obj1 = world.create('foo')['id']
        obj2 = world.create('foo')['id']

        obj1_received = []
        world.receiveFor(obj1, obj1_received.append)

        obj2_received = []
        world.receiveFor(obj2, obj2_received.append)

        # obj1 emits everything it receives
        world.receiveFor(obj1, world.emitterFor(obj1))
        
        # obj2 emits everything it receives
        world.receiveFor(obj2, world.emitterFor(obj2))
        
        # obj2 receives emissions from obj1
        world.subscribeTo(obj1, world.receiverFor(obj2))

        # obj1 receives emissions from obj2
        world.subscribeTo(obj2, world.receiverFor(obj1))

        # we have a nice loop set up.  When this test fails, it is likely to
        # continue spinning forever.
        world.emit('echo', obj1)
        self.assertEqual(obj1_received, ['echo'], "Should have received the "
                         "message once")
        self.assertEqual(obj2_received, ['echo'], "Should have received the "
                         "message once")




