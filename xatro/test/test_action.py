from twisted.trial.unittest import TestCase
from zope.interface.verify import verifyObject

from mock import MagicMock

from xatro.interface import IAction
from xatro.world import World
from xatro.action import Move, Charge



class MoveTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, Move('foo', 'bar'))


    def test_execute(self):
        """
        Moving to a new location should:

            - Cause C{location} to be updated
            - Cause C{contents} to be updated
            - Subscribe the thing to the location's events
            - Subscribe the location to the thing's events
        """
        world = World(MagicMock())
        thing = world.create('thing')
        room = world.create('room')

        move = Move(thing['id'], room['id'])
        move.execute(world)

        self.assertEqual(thing['location'], room['id'], "Should set location")
        self.assertEqual(room['contents'], [thing['id']], "Should set contents")

        room_called = []
        world.receiveFor(room['id'], room_called.append)

        thing_called = []
        world.receiveFor(thing['id'], thing_called.append)

        world.emit('foo', room['id'])
        self.assertEqual(room_called, ['foo'],
                         "Room should receive room events")
        self.assertEqual(thing_called, ['foo'],
                         "Thing should receive room events")

        room_called.pop()
        thing_called.pop()

        world.emit('foo', thing['id'])
        self.assertEqual(room_called, ['foo'],
                         "Room should receive thing events")
        self.assertEqual(thing_called, ['foo'],
                         "Thing should receive thing events")


    def test_execute_inRoom(self):
        """
        If an object is already located in another container, then moving it
        should:
            - Unsubscribe from the location's events
            - Unsubscribe the location from the thing's events
            - Cause C{contents} to be updated.
        """
        world = World(MagicMock())
        thing = world.create('thing')['id']
        room1 = world.create('room1')['id']
        room2 = world.create('room2')['id']

        move1 = Move(thing, room1)
        move1.execute(world)

        move2 = Move(thing, room2)
        move2.execute(world)

        room1_called = []
        world.receiveFor(room1, room1_called.append)

        room2_called = []
        world.receiveFor(room2, room2_called.append)

        thing_called = []
        world.receiveFor(thing, thing_called.append)

        # emit from room1
        world.emit('foo', room1)
        self.assertEqual(thing_called, [], "Thing should detach from previous "
                         "room events")
        room1_called.pop()

        # emit from thing
        world.emit('bar', thing)
        self.assertEqual(thing_called, ['bar'], "Thing should see own events")
        self.assertEqual(room1_called, [], "Room1 should detach from thing"
                         " events")

        # room1 contents
        room1_obj = world.get(room1)
        self.assertEqual(room1_obj['contents'], [], "Should remove from "
                         "contents of room1")

        location = world.get(thing)['location']
        self.assertEqual(location, room2, "Should update the "
                         "location of the thing.  This is mostly to confirm "
                         "that the default moving behavior tested in the other "
                         "test happened.")


    def test_moveToNone(self):
        """
        Moving something to nowhere should result in the location being
        None.
        """
        world = World(MagicMock())
        thing = world.create('thing')['id']
        room1 = world.create('room1')['id']

        move1 = Move(thing, room1)
        move1.execute(world)

        move2 = Move(thing, None)
        move2.execute(world)

        room1_called = []
        world.receiveFor(room1, room1_called.append)

        thing_called = []
        world.receiveFor(thing, thing_called.append)

        # emit from room1
        world.emit('foo', room1)
        self.assertEqual(thing_called, [], "Thing should detach from previous "
                         "room events")
        room1_called.pop()

        # emit from thing
        world.emit('bar', thing)
        self.assertEqual(thing_called, ['bar'], "Thing should see own events")
        self.assertEqual(room1_called, [], "Room1 should detach from thing"
                         " events")

        # room1 contents
        room1_obj = world.get(room1)
        self.assertEqual(room1_obj['contents'], [], "Should remove from "
                         "contents of room1")

        location = world.get(thing)['location']
        self.assertEqual(location, None, "Should update the location")



class ChargeTest(TestCase):


    def test_charge(self):
        """
        Charging should add energy to the thing's energy pool and to the
        thing's created energy pool.
        """
        world = World(MagicMock())

        thing = world.create('thing')

        charge = Charge(thing['id'])
        charge.execute(world)

        self.assertEqual(len(thing['energy']), 1)
        self.assertEqual(thing['created_energy'], 1, "Should keep track "
                         "of the energy it created")

        e = world.get(thing['energy'][0])
        self.assertEqual(e['kind'], 'energy')
        self.assertEqual(e['creator'], thing['id'])








