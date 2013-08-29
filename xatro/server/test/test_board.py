from twisted.trial.unittest import TestCase
from twisted.internet import defer
from zope.interface.verify import verifyObject

from mock import MagicMock, create_autospec

from xatro.server.interface import IEventReceiver, IKillable
from xatro.server.event import Event
from xatro.server.board import Square, Pylon, Material, Bot, Energy
from xatro.server.board import EnergyNotConsumedYet, NotEnoughEnergy
from xatro.server.board import YouAreTooDead


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


    def test_damageToDeath(self):
        """
        If you damage a bot sufficiently, it is dead.
        """
        b = Bot('foo', 'bob')
        b.square = MagicMock()
        b.emit = create_autospec(b.emit)

        b.damage(14)
        b.emit.assert_any_call(Event(b, 'died', None))
        self.assertEqual(b.hitpoints(), 0)


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

        # when dead, you can't do much
        self.assertRaises(YouAreTooDead, b.damage, 2)
        self.assertRaises(YouAreTooDead, b.revive, 2)
        self.assertRaises(YouAreTooDead, b.kill)
        self.assertRaises(YouAreTooDead, b.charge)
        self.assertRaises(YouAreTooDead, b.receiveEnergies, [])
        self.assertRaises(YouAreTooDead, b.consumeEnergy, 1)
        self.assertRaises(YouAreTooDead, b.shareEnergy, 2, None)


    def test_kill_energy(self):
        """
        When a bot is killed, any energy they shared should be removed.
        """
        b1 = Bot('foo', 'bob')
        b1.square = MagicMock()
        b2 = Bot('foo', 'jim')
        b2.emit = create_autospec(b2.emit)

        b1.charge()
        b1.shareEnergy(1, b2)
        b2.emit.reset_mock()

        b1.kill()
        self.assertEqual(b1.generated_energy, None)
        self.assertEqual(b2.energy_pool, [], "Should remove energy from other "
                         "bot's pool")
        b2.emit.assert_called_once_with(Event(b2, 'e.wasted', 1))


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
        self.assertEqual(b.energy_pool, [b.generated_energy])
        b.emit.assert_any_call(Event(b, 'charged', None))


    def test_charge_tooSoon(self):
        """
        It is an error to try and charge when there's still a generated_energy.
        """
        b = Bot('foo', 'bob')
        b.charge()
        self.assertRaises(EnergyNotConsumedYet, b.charge)


    def test_charge_energyConsumed(self):
        """
        After energy is consumed, it is okay to charge more.
        """
        b = Bot('foo', 'bob')
        b.charge()

        # bot consumes it
        b.consumeEnergy(1)
        b.charge()

        # someone else consumes it
        b.generated_energy.consume()
        b.charge()


    def test_canCharge(self):
        """
        An uncharged bot can charge.
        """
        b = Bot('foo', 'bob')
        self.assertEqual(b.canCharge().called, True)


    def test_canCharge_waiting(self):
        """
        A charged bot can't charge until the charge has been used.
        """
        b = Bot('foo', 'bob')
        b.charge()
        d = b.canCharge()
        self.assertEqual(d.called, False)
        b.consumeEnergy(1)
        self.assertEqual(d.called, True)


    def test_receiveEnergies(self):
        """
        A bot can receive energy.
        """
        b = Bot('foo', 'bob')
        b.emit = create_autospec(b.emit)
        energy = Energy()
        b.receiveEnergies([energy])
        self.assertIn(energy, b.energy_pool, "Bot should know it has it")
        b.emit.assert_called_once_with(Event(b, 'e.received', 1))


    def test_consumeEnergy(self):
        """
        A bot can consume energy in its pool, which will cause the energy to be
        removed from the pool, and an event to be emitted.
        """
        b = Bot('foo', 'bob')
        b.emit = create_autospec(b.emit)
        energy = Energy()
        b.receiveEnergies([energy])
        b.emit.reset_mock()
        
        b.consumeEnergy(1)
        self.assertEqual(self.successResultOf(energy.done()), 'consumed')
        self.assertEqual(b.energy_pool, [])
        b.emit.assert_called_once_with(Event(b, 'e.consumed', 1))


    def test_consumeEnergy_notEnough(self):
        """
        An error is raised if you try to consume energy you don't have.
        """
        b = Bot('foo', 'bob')
        energy = Energy()
        b.receiveEnergies([energy])

        self.assertRaises(NotEnoughEnergy, b.consumeEnergy, 2)
        self.assertEqual(len(b.energy_pool), 1, "Should not remove it")


    def test_shareEnergy(self):
        """
        A bot can share energy with other bots.
        """
        bot1 = Bot('foo', 'bob')
        bot1.charge()
        bot1.emit = create_autospec(bot1.emit)
        e = bot1.generated_energy

        bot2 = Bot('foo', 'hey')
        bot2.receiveEnergies = create_autospec(bot2.receiveEnergies)

        bot1.shareEnergy(1, bot2)
        bot2.receiveEnergies.assert_called_once_with([e])
        bot1.emit.assert_any_call(Event(bot1, 'e.shared', bot2))
        self.assertEqual(bot1.energy_pool, [], "Should remove from bot1")


    def test_shareEnergy_notEnough(self):
        """
        An error is raised if you try to share energy that you don't have.
        """
        bot1 = Bot('foo', 'bob')
        bot1.charge()

        bot2 = Bot('foo', 'jim')
        self.assertRaises(NotEnoughEnergy, bot1.shareEnergy, 2, bot2)



class EnergyTest(TestCase):


    def test_attributes(self):
        """
        Should know the bot who made me.
        """
        e = Energy()
        self.assertTrue(isinstance(e.done(), defer.Deferred))


    def test_consume(self):
        """
        Consuming energy will cause the callback to be called with 'consume'
        """
        e = Energy()
        d = e.done()
        e.consume()
        self.assertEqual(self.successResultOf(e.done()), 'consumed')
        self.assertEqual(self.successResultOf(d), 'consumed')


    def test_waste(self):
        """
        Wasting energy will cause the callback to be called with 'waste'
        """
        e = Energy()
        d = e.done()
        e.waste()
        self.assertEqual(self.successResultOf(e.done()), 'wasted')
        self.assertEqual(self.successResultOf(d), 'wasted')


