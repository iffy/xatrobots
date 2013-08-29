from twisted.trial.unittest import TestCase
from twisted.internet import defer
from zope.interface.verify import verifyObject

from mock import MagicMock, create_autospec

from xatro.server.interface import IEventReceiver, IKillable, ILocatable
from xatro.server.event import Event
from xatro.server.board import Square, Pylon, Ore, Lifesource, Bot, Energy
from xatro.server.board import Tool
from xatro.server.board import EnergyNotConsumedYet, NotEnoughEnergy
from xatro.server.board import TooDead, LackingTool


class SquareTest(TestCase):


    def test_attributes(self):
        """
        A Square should have bots, things, a pylon and a board.
        """
        q = Square('board')
        self.assertEqual(q.board, 'board')
        self.assertEqual(q.contents(), [])
        self.assertEqual(q.pylon, None)
        self.assertNotEqual(q.id, None)


    def test_IEventReceiver(self):
        verifyObject(IEventReceiver, Square(None))


    def test_eventReceived(self):
        """
        Should send the event to all the contents and to the board.
        """
        board = MagicMock()
        bot1 = Bot('A', 'bob')
        bot1.eventReceived = create_autospec(bot1.eventReceived)

        bot2 = Bot('B', 'bob')
        bot2.eventReceived = create_autospec(bot2.eventReceived)
        q = Square(board)
        q.addThing(bot1)
        q.addThing(bot2)

        q.eventReceived('hey')

        board.eventReceived.assert_any_call('hey')
        bot1.eventReceived.assert_any_call('hey')
        bot2.eventReceived.assert_any_call('hey')


    def test_eventReceived_nonEventReceivingContents(self):
        """
        If a thing in the square's contents doesn't receive events, it should
        not cause a problem
        """
        class Foo(object):
            square = None
        thing = Foo()
        thing.id = '12'
        q = Square(MagicMock())
        q.addThing(thing)

        q.eventReceived('hey')


    def test_addThing(self):
        """
        A thing added to a square will cause an event to be emitted, add the
        thing to the contents list and set the thing's square.
        """
        q = Square('board')
        q.eventReceived = MagicMock()

        thing = MagicMock()
        thing.id = 'hey'

        q.addThing(thing)

        self.assertEqual(thing.square, q, "Should set .square attribute")
        self.assertIn(thing, q.contents())
        q.eventReceived.assert_any_call(Event(thing, 'entered', q))


    def test_removeThing(self):
        """
        A thing removed from square will cause an event to be emitted, be
        removed from the square's contents and have thing.square set to None
        """
        q = Square('board')
        q.eventReceived = MagicMock()

        thing = MagicMock()
        thing.id = 'ho'
        
        q.addThing(thing)

        q.removeThing(thing)
        self.assertEqual(thing.square, None, "Should unset .square")
        self.assertNotIn(thing, q.contents())
        q.eventReceived.assert_any_call(Event(thing, 'exited', q))


    def test_addThing_removeFromOther(self):
        """
        A thing added to a square should be removed from the other square.
        """
        q1 = Square(MagicMock())
        q2 = Square(MagicMock())

        thing = MagicMock()
        thing.id = 'hey'
        q1.addThing(thing)
        q2.addThing(thing)
        self.assertNotIn(thing.id, q1.contents())
        self.assertEqual(thing.square, q2)


    def test_contents(self):
        """
        You can list the things on a square.
        """
        q = Square(MagicMock())

        a, b = Ore(), Ore()
        q.addThing(a)
        q.addThing(b)
        
        self.assertEqual(set(q.contents()), set([a, b]))



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



class OreTest(TestCase):


    def test_ILocatable(self):
        verifyObject(ILocatable, Ore())



class ToolTest(TestCase):


    def test_attributes(self):
        """
        All tools have a type/kind.
        """
        tool = Tool('foo')
        self.assertEqual(tool.kind, 'foo')


    def test_destroyed(self):
        """
        Should return a Deferred which fires when killed.
        """
        tool = Tool('foo')
        d1 = tool.destroyed()
        d2 = tool.destroyed()
        tool.kill()
        self.assertEqual(self.successResultOf(d1), tool)
        self.assertEqual(self.successResultOf(d2), tool)



class LifesourceTest(TestCase):


    def test_emit(self):
        """
        Emitting when there's a square should call the square's eventReceived
        method.
        """
        s = Lifesource(MagicMock())
        s.square = MagicMock()
        s.emit('foo')
        s.square.eventReceived.assert_called_once_with('foo')


    def test_emit_noSquare(self):
        """
        Emitting when there's no square should be a nop
        """
        s = Lifesource(MagicMock())
        s.emit('foo')


    def test_ILocatable(self):
        verifyObject(ILocatable, Lifesource(MagicMock()))


    def test_IKillable(self):
        verifyObject(IKillable, Lifesource(MagicMock()))


    def test_hitpoints(self):
        """
        Should have hitpoints
        """
        s = Lifesource(MagicMock())
        self.assertTrue(s.hitpoints() > 0)


    def test_damage(self):
        """
        You can damage a lifesource
        """
        s = Lifesource(MagicMock())
        s.emit = create_autospec(s.emit)
        hp = s.hitpoints()

        s.damage(2)
        self.assertEqual(s.hitpoints(), hp-2)
        s.emit.assert_called_once_with(Event(s, 'hp', -2))


    def test_damageToDeath(self):
        """
        Excessive damage will kill a Lifesource
        """
        s = Lifesource(MagicMock())
        s.kill = create_autospec(s.kill)

        s.damage(s.hitpoints()+2)
        self.assertEqual(s.hitpoints(), 0)
        s.kill.assert_called_once_with()


    def test_revive(self):
        """
        You can restore health of a lifesource
        """
        s = Lifesource(MagicMock())
        s.emit = create_autospec(s.emit)
        hp = s.hitpoints()

        s.damage(3)
        s.emit.reset_mock()

        s.revive(2)
        self.assertEqual(s.hitpoints(), hp-1)
        s.emit.assert_called_once_with(Event(s, 'hp', 2))


    def test_kill(self):
        """
        A lifesource can be killed, and once killed, will be dead.
        """
        obj = MagicMock()
        s = Lifesource(obj)
        s.square = MagicMock()
        s.emit = create_autospec(s.emit)

        s.kill()
        self.assertEqual(s.hitpoints(), 0)
        s.emit.assert_called_once_with(Event(s, 'died', None))

        # should kill the thing it's a lifesource for.
        obj.kill.assert_called_once_with()

        # things that can't be done when killed
        self.assertRaises(TooDead, s.damage, 2)
        self.assertRaises(TooDead, s.revive, 2)
        self.assertRaises(TooDead, s.kill)


    def test_kill_revertToOre(self):
        """
        A killed lifesource will revert to a piece of Ore.
        """
        s = Lifesource(MagicMock())

        square = Square(MagicMock())
        square.addThing(s)

        s.kill()

        self.assertNotIn(s, square.contents(), "The lifesource should not be "
                         "on the square anymore")
        contents = square.contents()
        self.assertTrue(isinstance(contents[0], Ore), "Should put ore back")


    def test_kill_otherDead(self):
        """
        If the other is already dead, don't raise an exception when I die.
        """
        obj = MagicMock()
        obj.kill.side_effect = TooDead()

        s = Lifesource(obj)
        s.square = MagicMock()
        s.kill()


    def test_noticeDestruction(self):
        """
        If the other thing I'm a support for is destroyed, I should notice.
        """
        tool = Tool('gummy bear')
        s = Lifesource(tool)
        s.kill = create_autospec(s.kill)
        tool.kill()
        s.kill.assert_called_once_with()




class BotTest(TestCase):


    def test_attributes(self):
        """
        Should have health, energy, a name, tool, a portal, a square,
        a team.
        """
        b = Bot('foo', 'bob')
        self.assertEqual(b.health, 10)
        self.assertEqual(b.energy_pool, [])
        self.assertEqual(b.generated_energy, None)
        self.assertEqual(b.name, 'bob')
        self.assertEqual(b.team, 'foo')
        self.assertEqual(b.tool, None)
        self.assertEqual(b.portal, None)
        self.assertEqual(b.square, None)
        self.assertNotEqual(b.id, None)


    def test_ILocatable(self):
        verifyObject(ILocatable, Bot(None, None))


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
        b.emit.assert_called_once_with(Event(b, 'hp', -3))


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
        b.emit.assert_called_once_with(Event(b, 'hp', 2))


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
        b.square.removeThing.assert_called_once_with(b)

        # when dead, you can't do much
        self.assertRaises(TooDead, b.damage, 2)
        self.assertRaises(TooDead, b.revive, 2)
        self.assertRaises(TooDead, b.kill)
        self.assertRaises(TooDead, b.charge)
        self.assertRaises(TooDead, b.receiveEnergies, [])
        self.assertRaises(TooDead, b.consumeEnergy, 1)
        self.assertRaises(TooDead, b.shareEnergy, 2, None)
        self.assertRaises(TooDead, b.equip, Tool('foo'))
        self.assertRaises(TooDead, b.shoot, None, 4)


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


    def test_equip(self):
        """
        You can equip a tool.
        """
        bot = Bot('foo', 'bob')
        bot.emit = create_autospec(bot.emit)

        tool = Tool('car')
        bot.equip(tool)
        self.assertEqual(bot.tool, tool)
        bot.emit.assert_called_once_with(Event(bot, 'equipped', tool))


    def test_toolDestroyed(self):
        """
        When a tool is destroyed, it is unequipped from the bot.
        """
        bot = Bot('foo', 'bob')
        bot.emit = create_autospec(bot.emit)

        tool = Tool('balloon')
        bot.equip(tool)
        bot.emit.reset_mock()

        tool.kill()
        self.assertEqual(bot.tool, None, "Should unequip")
        bot.emit.assert_called_once_with(Event(bot, 'unequipped', None))


    def test_shoot(self):
        """
        You can shoot another thing with a cannon
        """
        bot1 = Bot('foo', 'bob')
        bot1.emit = create_autospec(bot1.emit)
        bot2 = Bot('foo', 'victim')

        bot1.equip(Tool('cannon'))
        bot1.emit.reset_mock()

        hp = bot2.hitpoints()

        bot1.shoot(bot2, 3)
        self.assertEqual(bot2.hitpoints(), hp-3)
        bot1.emit.assert_called_once_with(Event(bot1, 'shot', bot2))


    def test_shoot_noCannon(self):
        """
        You can't shoot without a cannon, or with a cat.
        """
        bot1 = Bot('foo', 'bob')
        bot2 = Bot('foo', 'bill')
        self.assertRaises(LackingTool, bot1.shoot, bot2, 2)

        bot1.tool = Tool('cat')
        self.assertRaises(LackingTool, bot1.shoot, bot2, 2)        




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


