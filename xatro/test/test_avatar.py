from twisted.trial.unittest import TestCase

from mock import MagicMock

from xatro.error import NotAllowed
from xatro.world import World
from xatro.avatar import Avatar



class AvatarTest(TestCase):


    def test_availableCommands(self):
        """
        An avatar has a list of available command classes.
        """
        a = Avatar()
        self.assertEqual(a.availableCommands(), [])
        a._available_commands.append('foo')
        self.assertEqual(a.availableCommands(), ['foo'])


    def test_game_piece(self):
        """
        An avatar has a game piece.
        """
        a = Avatar()
        self.assertEqual(a._game_piece, None)


    def test_setGamePiece(self):
        """
        Connecting an avatar to a game piece will make the avatar subscribe
        to the events of that game piece.
        """
        world = World(MagicMock())

        a = Avatar(world)
        a.eventReceived = MagicMock()

        piece = world.create('foo', receive_emissions=False)
        a.setGamePiece(piece['id'])
        self.assertEqual(a._game_piece, piece['id'])

        world.eventReceived('hey', piece['id'])
        a.eventReceived.assert_called_once_with('hey')

        a.eventReceived.reset_mock()
        world.emit('foo', piece['id'])
        self.assertEqual(a.eventReceived.call_count, 0, "Should only receive "
                         "things the game piece receives, not subscribe to "
                         "things the game piece emits.")


    def test_setGamePiece_twice(self):
        """
        You can't set the game piece twice.
        """
        a = Avatar(MagicMock())
        a.setGamePiece('foo')
        self.assertRaises(NotAllowed, a.setGamePiece, 'bar')


    def test_eventReceived(self):
        """
        Events should be saved until something connects which will be called
        with all the events.
        """
        # before receiver
        a = Avatar()
        a.eventReceived('1')
        a.eventReceived('2')

        # on attaching
        called = []
        a.setEventReceiver(called.append)
        self.assertEqual(called, ['1', '2'])

        # after attaching
        a.eventReceived('3')
        self.assertEqual(called, ['1', '2', '3'], "After attaching an "
                         "event receiver, all events should be sent immediately"
                         " to the receiver")


    def test_world(self):
        """
        An avatar knows about the world.
        """
        a = Avatar('foo')
        self.assertEqual(a._world, 'foo')


    def test_makeCommand(self):
        """
        makeCommand will instantiate the given class with the avatar's
        game piece as the first argument.
        """
        a = Avatar()
        a._game_piece = MagicMock()

        cls = MagicMock()
        cls.return_value = 'ret'

        cmd = a.makeCommand(cls, 'foo', 'bar', hey='fo')
        cls.assert_called_once_with(a._game_piece, 'foo', 'bar', hey='fo')
        self.assertEqual(cmd, 'ret')


    def test_execute(self):
        """
        A command executed by an avatar is just passed to the world to be
        executed.
        """
        world = MagicMock()
        world.execute.return_value = 'foo'

        a = Avatar(world)
        a.makeCommand = MagicMock()
        a.makeCommand.return_value = 'made command'
        
        command = MagicMock()
        r = a.execute(command, 'foo', 'bar')

        a.makeCommand.assert_called_once_with(command, 'foo', 'bar')
        world.execute.assert_called_once_with('made command')
        self.assertEqual(r, 'foo', "Should return result of execution")


