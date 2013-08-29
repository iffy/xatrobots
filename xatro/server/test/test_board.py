from twisted.trial.unittest import TestCase
from zope.interface.verify import verifyObject

from mock import MagicMock, create_autospec

from xatro.server.interface import IEventReceiver, IKillable
from xatro.server.event import Event
from xatro.server.board import Square, Pylon, Material, Bot, Energy


class SquareTest(TestCase):


    def test_attributes(self):
        """
        A Square should have bots, materials, a pylon and a board.
        """
        q = Square('board')
        self.assertEqual(q.board, 'board')
        self.assertEqual(q.bots, {})
        self.assertEqual(q.materials, {})
        self.assertEqual(q.pylon, None)
        self.assertNotEqual(q.id, None)


    def test_IEventReceiver(self):
        verifyObject(IEventReceiver, Square(None))


    def test_eventReceived(self):
        """
        Should send the event to all the bots and to the board.
        """
        board = MagicMock()
        bot1 = Bot('A', 'bob')
        bot1.eventReceived = create_autospec(bot1.eventReceived)

        bot2 = Bot('B', 'bob')
        bot2.eventReceived = create_autospec(bot2.eventReceived)
        q = Square(board)
        q.addBot(bot1)
        q.addBot(bot2)

        q.eventReceived('hey')

        board.eventReceived.assert_any_call('hey')
        bot1.eventReceived.assert_any_call('hey')
        bot2.eventReceived.assert_any_call('hey')


    def test_addBot(self):
        """
        A bot added to a square will cause an event to be emitted, add the bot
        to the bot list and set the bot's square.
        """
        q = Square('board')
        called = []
        q.eventReceived = called.append

        bot1 = Bot('A', 'bob')
        q.addBot(bot1)

        self.assertEqual(bot1.square, q,
                         "Should tell the bot it is on the square")
        self.assertIn(bot1.id, q.bots, "Should have bot1 in square")
        self.assertEqual(called, [Event(bot1, 'entered', q)])


    def test_removeBot(self):
        """
        A bot removed from square will cause an event to be emitted, be
        removed from the square's list and have bot.square set to None
        """
        q = Square('board')
        q.eventReceived = MagicMock()

        bot1 = Bot('A', 'bob')
        q.addBot(bot1)

        q.removeBot(bot1)
        self.assertEqual(bot1.square, None, "Should remove bot's square")
        self.assertNotIn(bot1.id, q.bots, "Should remove from botlist")
        q.eventReceived.assert_any_call(Event(bot1, 'exited', q))



    def test_addBot_removeFromOther(self):
        """
        A bot added to a square should be removed from the other square.
        """
        q1 = Square(MagicMock())
        q2 = Square(MagicMock())

        bot = Bot('a', 'bob')
        q1.addBot(bot)
        q2.addBot(bot)
        self.assertNotIn(bot.id, q1.bots)




class PylonTest(TestCase):


    def test_attributes(self):
        """
        A Pylon should belong to a team, have locks and the work required to
        unlock the lock.
        """
        p = Pylon(3)
        self.assertEqual(p.square, None)
        self.assertEqual(p.locks, 3)
        self.assertEqual(p.team, None)
        self.assertEqual(p.unlock_work, None)
        self.assertEqual(p.lock_work, None)



class MaterialTest(TestCase):


    def test_attributes(self):
        """
        Should have a use and a health
        """
        m = Material()
        self.assertEqual(m.square, None)
        self.assertEqual(m.health, None)
        self.assertEqual(m.current_use, None)
        self.assertNotEqual(m.id, None)



class BotTest(TestCase):


    def test_attributes(self):
        """
        Should have health, energy, a name, equipment, a portal, a square,
        a team.
        """
        b = Bot('foo', 'bob')
        self.assertEqual(b.health, 10)
        self.assertEqual(b.energy_pool, [])
        self.assertEqual(b.generated_energy, None)
        self.assertEqual(b.name, 'bob')
        self.assertEqual(b.team, 'foo')
        self.assertEqual(b.equipment, None)
        self.assertEqual(b.portal, None)
        self.assertEqual(b.square, None)
        self.assertNotEqual(b.id, None)


    def test_IEventReceiver(self):
        verifyObject(IEventReceiver, Bot('foo', 'bob'))


    def test_eventReceived(self):
        """
        If this bot has an event_receiver, it should be called with events,
        otherwise, it shouldn't.
        """
        b1 = Bot('foo', 'bob')
        b1.eventReceived('foo')

        called = []
        b2 = Bot('hey', 'ho', called.append)
        b2.eventReceived('hey')
        self.assertEqual(called, ['hey'])


    def test_emit(self):
        """
        Emitting when there's a square should call the square's eventReceived
        method.
        """
        b = Bot('foo', 'bob')
        b.square = MagicMock()
        b.emit('foo')
        b.square.eventReceived.assert_called_once_with('foo')


    def test_emit_noSquare(self):
        """
        Emitting when there's no square should call the bot's eventReceived
        method.
        """
        b = Bot('foo', 'bob')
        b.eventReceived = create_autospec(b.eventReceived)
        b.emit('foo')
        b.eventReceived.assert_called_once_with('foo')


    def test_IKillable(self):
        verifyObject(IKillable, Bot('foo', 'bob'))


    def test_damage(self):
        """
        Should diminish a bot's health and notify the square.
        """
        b = Bot('foo', 'bob')
        b.emit = create_autospec(b.emit)

        b.damage(3)
        self.assertEqual(b.hitpoints(), 7)
        b.emit.assert_called_once_with(Event(b, 'health', -3))


    def test_revive(self):
        """
        Should increase the bot's health
        """
        b = Bot('foo', 'bob')
        b.damage(4)

        b.emit = create_autospec(b.emit)

        b.revive(2)
        self.assertEqual(b.hitpoints(), 8)
        b.emit.assert_called_once_with(Event(b, 'health', 2))


    def test_kill(self):
        """
        Should set a bot's health to 0, send notification to the square,
        and remove them from the square
        """
        b = Bot('foo', 'bob')
        b.square = MagicMock()
        b.emit = create_autospec(b.emit)

        b.kill()
        self.assertEqual(b.hitpoints(), 0)
        b.emit.assert_called_once_with(Event(b, 'died', None))
        b.square.removeBot.assert_called_once_with(b)


    def test_kill_energy(self):
        """
        When a bot is killed, all energy they shared should be removed.
        """
        self.fail('write me')


    def test_charge(self):
        """
        A bot can charge, making a new generated_energy which is added to the
        energy_pool.
        """
        b = Bot('foo', 'bob')
        b.emit = create_autospec(b.emit)

        b.charge()
        self.assertTrue(isinstance(b.generated_energy, Energy),
                        "Should set generated_energy")
        self.assertEqual(b.generated_energy.bot, b,
                         "Energy should know about bot")
        b.emit.assert_called_once_with(Event(b, 'charged', None))


        



class EnergyTest(TestCase):


    def test_attributes(self):
        """
        Should know the bot who made me.
        """
        bot = object()
        e = Energy(bot)
        self.assertEqual(e.bot, bot)


