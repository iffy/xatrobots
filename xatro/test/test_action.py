from twisted.trial.unittest import TestCase

from mock import MagicMock

from xatro.world import World
from xatro.action import Move



class MoveTest(TestCase):


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

        world.emit('foo')
        self.assertEqual(room_called, [])
        self.assertEqual(thing_called, [])

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





