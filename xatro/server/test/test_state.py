from twisted.trial.unittest import TestCase
from zope.interface.verify import verifyObject

from mock import MagicMock

from xatro.server.board import Square, Board, Bot, Ore, Pylon, Tool
from xatro.server.event import Event
from xatro.server.state import GameState
from xatro.server.interface import IEventReceiver


class GameStateTest(TestCase):


    def test_IEventReceiver(self):
        verifyObject(IEventReceiver, GameState())


    def test_dict(self):
        """
        Events can either be filled with dicts or objects.
        """
        s = GameState()
        square = Square(None)
        board = Board()

        s.handle_foo = MagicMock()

        # objects
        s.eventReceived(Event(board, 'foo', square))
        s.handle_foo.assert_called_once_with(
            Event(board.toDict(), 'foo', square.toDict()))

        s.handle_foo.reset_mock()

        # dict
        s.eventReceived(Event(board.toDict(), 'foo', square.toDict()))
        s.handle_foo.assert_called_once_with(
            Event(board.toDict(), 'foo', square.toDict()))


    def test_bots_joined_quit(self):
        """
        Should keep track of bots that come and go.
        """
        s = GameState()
        bot = Bot('foo', 'bob')

        s.eventReceived(Event(bot, 'joined', None))
        self.assertEqual(s.objects[bot.id], {
            'id': bot.id,
            'object': 'bot',
            'hp': bot.hitpoints(),
            'energy': 0,
            'team': 'foo',
            'name': 'bob',
            'tool': None,
        })

        s.eventReceived(Event(bot, 'quit', None))
        self.assertNotIn(bot.id, s.objects)


    def test_squares(self):
        """
        Should keep track of squares in the squares dict.
        """
        s = GameState()
        square = Square(None)
        square.coordinates = (9, 2)
        board = Board()

        s.eventReceived(Event(board, 'square_added', square))
        self.assertEqual(s.objects[square.id], {
            'id': square.id,
            'object': 'square',
            'coordinates': (9, 2),
            'contents': {
                'pylon': [],
                'ore': [],
                'bot': [],
                'lifesource': [],
            },
        })


    def test_obj_entered_exited(self):
        """
        Should keep track of objects entering and exiting squares.
        """
        s = GameState()
        square = Square(None)
        pylon = Pylon()

        s.eventReceived(Event(pylon, 'entered', square))
        self.assertEqual(s.objects[square.id]['contents']['pylon'], [pylon.id])
        self.assertEqual(s.objects[pylon.id], {
            'id': pylon.id,
            'object': 'pylon',
            'locks': pylon.locks,
            'team': pylon.team,
        })

        s.eventReceived(Event(pylon, 'exited', square))
        self.assertEqual(s.objects[square.id]['contents']['pylon'], [])
        self.assertNotIn(pylon.id, s.objects)


    def test_obj_entered_preserveSquare(self):
        """
        If two objects enter a square, don't overwrite the contents.
        """
        s = GameState()
        square = Square(None)
        o1 = Ore()
        o2 = Ore()

        s.eventReceived(Event(o1, 'entered', square))
        s.eventReceived(Event(o2, 'entered', square))
        self.assertEqual(len(s.objects[square.id]['contents']['ore']), 2)


    def test_bot_exited(self):
        """
        A bot exiting should not remove it from the objects list.
        """
        s = GameState()
        square = Square(None)
        bot = Bot('foo', 'bar')

        s.eventReceived(Event(bot, 'entered', square))
        s.eventReceived(Event(bot, 'exited', square))
        self.assertIn(bot.id, s.objects, "Bots leaving a square doesn't "
                      "warrant removal from the game")


    def test_pylon_locks(self):
        """
        Updates to the number of locks on a pylon should be kept track of
        """
        s = GameState()
        square = Square(None)
        pylon = Pylon()

        s.eventReceived(Event(pylon, 'entered', square))
        s.eventReceived(Event(pylon, 'pylon_locks', 12))
        self.assertEqual(s.objects[pylon.id]['locks'], 12)


    def test_lock_broken(self):
        """
        Broken locks cause the locks number to be updated
        """
        s = GameState()
        square = Square(None)
        pylon = Pylon()

        s.eventReceived(Event(pylon, 'entered', square))
        s.eventReceived(Event(pylon, 'pylon_locks', 12))
        s.eventReceived(Event(None, 'lock_broken', pylon))
        self.assertEqual(s.objects[pylon.id]['locks'], 11)


    def test_lock_added(self):
        """
        Added locks cause the locks number to be updated
        """
        s = GameState()
        square = Square(None)
        pylon = Pylon()

        s.eventReceived(Event(pylon, 'entered', square))
        s.eventReceived(Event(pylon, 'pylon_locks', 12))
        s.eventReceived(Event(None, 'lock_added', pylon))
        self.assertEqual(s.objects[pylon.id]['locks'], 13)


    def test_pylon_captured(self):
        """
        Captured pylons should result in a team name update
        """
        s = GameState()
        square = Square(None)
        pylon = Pylon()
        bot = Bot('team', 'foo')

        s.eventReceived(Event(pylon, 'entered', square))
        s.eventReceived(Event(bot, 'pylon_captured', pylon))
        self.assertEqual(s.objects[pylon.id]['team'], 'team')


    def test_hp(self):
        """
        Hitpoint changes should result in hitpoint changes
        """
        s = GameState()
        square = Square(None)
        bot = Bot('hey', 'ho')

        s.eventReceived(Event(bot, 'entered', square))
        s.eventReceived(Event(bot, 'hp_set', 48))
        self.assertEqual(s.objects[bot.id]['hp'], 48)
        s.eventReceived(Event(bot, 'hp', 12))
        self.assertEqual(s.objects[bot.id]['hp'], 60)


    def test_energy(self):
        """
        Energy changes should result in the energy level changing.
        """
        s = GameState()
        square = Square(None)
        bot = Bot('hey', 'ho')

        s.eventReceived(Event(bot, 'entered', square))
        s.eventReceived(Event(bot, 'e_change', 1))
        self.assertEqual(s.objects[bot.id]['energy'], 1)


    def test_tool(self):
        """
        Tool changes should be noticed
        """
        s = GameState()
        square = Square(None)
        bot = Bot('hey', 'ho')

        s.eventReceived(Event(bot, 'entered', square))
        s.eventReceived(Event(bot, 'equipped', Tool('knife')))
        self.assertEqual(s.objects[bot.id]['tool'], 'knife')
        s.eventReceived(Event(bot, 'unequipped', None))
        self.assertEqual(s.objects[bot.id]['tool'], None)







