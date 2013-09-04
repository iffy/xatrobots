from twisted.trial.unittest import TestCase

from mock import MagicMock

from xatro.world import World
from xatro.event import Created, Destroyed, AttrSet, Moved


class WorldTest(TestCase):


    def test_init(self):
        """
        A world has an event receiver that will be supplied with all the
        events.
        """
        called = []
        world = World(called.append)
        world.eventReceived('foo')
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


    def test_destroy_withinContainer(self):
        """
        If you destroy something when it's in a container, remove it from the
        container.
        """
        ev = MagicMock()
        world = World(ev)
        obj = world.create('foo')
        container = world.create('cont')
        world.move(obj['id'], container['id'])

        ev.reset_mock()
        world.destroy(obj['id'])

        self.assertNotIn(obj['id'], world.objects[container['id']]['contents'])
        self.assertEqual(obj['location'], None)


    def test_move(self):
        """
        You can put objects inside other objects.
        """
        ev = MagicMock()
        world = World(ev)
        c1 = world.create('container')
        c2 = world.create('container')
        thing = world.create('bar')

        ev.reset_mock()

        world.move(thing['id'], c1['id'])
        ev.assert_any_call(Moved(thing['id'], None, c1['id']))
        obj = world.get(c1['id'])
        self.assertIn(thing['id'], obj['contents'])
        self.assertEqual(thing['location'], c1['id'])

        ev.reset_mock()

        world.move(thing['id'], c2['id'])
        ev.assert_any_call(Moved(thing['id'], c1['id'], c2['id']))
        c1 = world.get(c1['id'])
        c2 = world.get(c2['id'])
        self.assertNotIn(thing['id'], c1['contents'])
        self.assertIn(thing['id'], c2['contents'])
        self.assertEqual(thing['location'], c2['id'])

        ev.reset_mock()

        world.move(thing['id'], None)
        ev.assert_any_call(Moved(thing['id'], c2['id'], None))
        self.assertNotIn(thing['id'], c2['contents'])





