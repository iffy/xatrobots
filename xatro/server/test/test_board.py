from twisted.trial.unittest import TestCase
from twisted.internet import defer
from zope.interface.verify import verifyObject

from mock import MagicMock, create_autospec

from xatro.server.interface import IEventReceiver, IKillable, ILocatable
from xatro.server.interface import IWorkMaker
from xatro.server.event import Event
from xatro.server.board import Square, Pylon, Ore, Lifesource, Bot, Energy
from xatro.server.board import Tool
from xatro.server.board import EnergyNotConsumedYet, NotEnoughEnergy
from xatro.server.board import NotOnSquare, LackingTool, NotAllowed
from xatro.work import Work


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


    def test_IWorkMaker(self):
        verifyObject(IWorkMaker, Square(None))


    def test_workFor(self):
        """
        I just ask the Board.
        """
        board = MagicMock()
        board.workFor.return_value = 'foo'
        
        square = Square(board)
        ret = square.workFor('joe', 'eat', 'ice cream')
        board.workFor.assert_called_once_with('joe', 'eat', 'ice cream')
        self.assertEqual(ret, 'foo')


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


    def test_contents_Class(self):
        """
        You can list only instances of a given class.
        """
        q = Square(MagicMock())

        o1, o2 = Ore(), Ore()
        b = Bot('foo', 'bar')
        ls = Lifesource()

        q.addThing(o1)
        q.addThing(o2)
        q.addThing(b)
        q.addThing(ls)

        self.assertEqual(q.contents(Lifesource), [ls])
        self.assertEqual(q.contents(Bot), [b])



class PylonTest(TestCase):


    def test_ILocatable(self):
        verifyObject(ILocatable, Pylon())


    def test_attributes(self):
        """
        A Pylon should belong to a team, have locks and the work required to
        unlock the lock.
        """
        p = Pylon()
        self.assertEqual(p.square, None)
        self.assertEqual(p.team, None)
        self.assertEqual(p.tobreak, None)
        self.assertEqual(p.tolock, None)


    def test_emit(self):
        """
        Emitting should send the event to the containing Square.
        """
        p = Pylon()
        p.square = MagicMock()
        p.emit('foo')
        p.square.eventReceived.assert_called_once_with('foo')


    def test_emit_noSquare(self):
        """
        Emitting with no square is a nop
        """
        p = Pylon()
        p.emit('foo')


    def test_setLocks(self):
        """
        You can set the number of locks on a Pylon
        """
        p = Pylon()
        p.emit = create_autospec(p.emit)
        p.setLocks(6)
        p.emit.assert_called_once_with(Event(p, 'pylon.locks', 6))
        self.assertEqual(p.locks, 6)
        

    def test_setLockWork(self):
        """
        You can set the Work required to lock a Pylon
        """
        p = Pylon()
        p.emit = create_autospec(p.emit)
        p.setLockWork('foo')
        p.emit.assert_called_once_with(Event(p, 'pylon.tolock', 'foo'))
        self.assertEqual(p.tolock, 'foo')


    def test_setBreakLockWork(self):
        """
        You can set the Work required to unlock a Pylon
        """
        p = Pylon()
        p.emit = create_autospec(p.emit)
        p.setBreakLockWork('bar')
        p.emit.assert_called_once_with(Event(p, 'pylon.tobreak', 'bar'))
        self.assertEqual(p.tobreak, 'bar')



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
        self.assertEqual(self.successResultOf(tool.destroyed()), tool)


    def test_optionalLifesource(self):
        """
        A tool can optionally know about its lifesource.
        """
        tool = Tool('foo', 'lifesource')
        self.assertEqual(tool.lifesource, 'lifesource')



class LifesourceTest(TestCase):


    def test_emit(self):
        """
        Emitting when there's a square should call the square's eventReceived
        method.
        """
        s = Lifesource()
        s.square = MagicMock()
        s.emit('foo')
        s.square.eventReceived.assert_called_once_with('foo')


    def test_emit_noSquare(self):
        """
        Emitting when there's no square should be a nop
        """
        s = Lifesource()
        s.emit('foo')


    def test_ILocatable(self):
        verifyObject(ILocatable, Lifesource())


    def test_IKillable(self):
        verifyObject(IKillable, Lifesource())


    def test_hitpoints(self):
        """
        Should have hitpoints
        """
        s = Lifesource()
        self.assertTrue(s.hitpoints() > 0)


    def test_damage(self):
        """
        You can damage a lifesource
        """
        s = Lifesource()
        s.square = MagicMock()
        s.emit = create_autospec(s.emit)
        hp = s.hitpoints()

        s.damage(2)
        self.assertEqual(s.hitpoints(), hp-2)
        s.emit.assert_called_once_with(Event(s, 'hp', -2))


    def test_damageToDeath(self):
        """
        Excessive damage will kill a Lifesource
        """
        s = Lifesource()
        s.square = MagicMock()
        s.kill = create_autospec(s.kill)

        s.damage(s.hitpoints()+2)
        self.assertEqual(s.hitpoints(), 0)
        s.kill.assert_called_once_with()


    def test_revive(self):
        """
        You can restore health of a lifesource
        """
        s = Lifesource()
        s.square = MagicMock()
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
        s = Lifesource()
        square = Square(MagicMock())
        square.addThing(s)

        obj = MagicMock()
        s.pairWith(obj)
        s.emit = create_autospec(s.emit)

        s.kill()
        self.assertEqual(s.hitpoints(), 0)
        s.emit.assert_called_once_with(Event(s, 'died', None))
        self.assertEqual(s.square, None)

        # should kill the thing it's a lifesource for.
        obj.kill.assert_called_once_with()

        # things that can't be done when killed
        self.assertRaises(NotOnSquare, s.damage, 2)
        self.assertRaises(NotOnSquare, s.revive, 2)
        self.assertRaises(NotOnSquare, s.kill)
        self.assertRaises(NotOnSquare, s.pairWith, 'anything')


    def test_kill_revertToOre(self):
        """
        A killed lifesource will revert to a piece of Ore.
        """
        s = Lifesource()

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
        obj.kill.side_effect = NotOnSquare()

        s = Lifesource()
        s.square = MagicMock()
        s.pairWith(obj)
        s.kill()


    def test_noticeDestruction(self):
        """
        If the other thing I'm a support for is destroyed, I should notice.
        """
        s = Lifesource()
        s.square = MagicMock()
        tool = Tool('gummy bear')
        s.pairWith(tool)
        s.kill = create_autospec(s.kill)
        tool.kill()
        s.kill.assert_called_once_with()


    def test_destroyed(self):
        """
        Should return a Deferred which fires when killed.
        """
        s = Lifesource()
        s.square = MagicMock()
        d1 = s.destroyed()
        d2 = s.destroyed()
        s.kill()
        self.assertEqual(self.successResultOf(d1), s)
        self.assertEqual(self.successResultOf(d2), s)
        self.assertEqual(self.successResultOf(s.destroyed()), s)


    def test_pairWith_another(self):
        """
        If you pair one thing with another thing, it should forget the old
        pairing.
        """
        s = Lifesource()
        s.square = MagicMock()
        tool1 = Tool('cow')
        s.pairWith(tool1)

        tool2 = Tool('milk')
        s.pairWith(tool2)

        tool1.kill()
        self.assertEqual(s.dead, False)



class BotTest(TestCase):

    num = 0

    def mkBot(self, real_square=False):
        num = self.num
        self.num += 1
        b = Bot('team%d' % (num,), 'bot%d' % (num,)) 
        if real_square:
            square = Square(MagicMock())
            square.addThing(b)
        else:
            b.square = MagicMock()
        b.emit = create_autospec(b.emit)
        return b


    def test_attributes(self):
        """
        Should have health, energy, a name, tool, a portal, a square,
        a team.
        """
        b = Bot('foo', 'bob')
        self.assertEqual(b.hitpoints(), 10)
        self.assertEqual(b.energy_pool, [])
        self.assertEqual(b.generated_energy, None)
        self.assertEqual(b.charging_work, None)
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
        b = self.mkBot()
        b.damage(3)
        self.assertEqual(b.hitpoints(), 7)
        b.emit.assert_called_once_with(Event(b, 'hp', -3))


    def test_damageToDeath(self):
        """
        If you damage a bot sufficiently, it is dead.
        """
        b = self.mkBot()
        b.damage(14)
        b.emit.assert_any_call(Event(b, 'died', None))
        self.assertEqual(b.hitpoints(), 0)


    def test_revive(self):
        """
        Should increase the bot's health
        """
        b = self.mkBot()
        b.damage(4)
        b.emit.reset_mock()

        b.revive(2)
        self.assertEqual(b.hitpoints(), 8)
        b.emit.assert_called_once_with(Event(b, 'hp', 2))


    def test_kill(self):
        """
        Should set a bot's health to 0, send notification to the square,
        and remove them from the square
        """
        b = self.mkBot()
        square = Square(MagicMock())
        square.addThing(b)

        b.kill()
        self.assertEqual(b.hitpoints(), 0)
        b.emit.assert_called_once_with(Event(b, 'died', None))
        self.assertEqual(b.square, None, "Should remove from square")
        b.emit.reset_mock()

        # when dead, you can't do much
        self.assertRaises(NotOnSquare, b.damage, 2)
        self.assertRaises(NotOnSquare, b.revive, 2)
        self.assertRaises(NotOnSquare, b.kill)
        self.assertRaises(NotOnSquare, b.charge)
        self.assertRaises(NotOnSquare, b.receiveEnergies, [])
        self.assertRaises(NotOnSquare, b.consumeEnergy, 1)
        self.assertRaises(NotOnSquare, b.shareEnergy, 2, None)
        self.assertRaises(NotOnSquare, b.equip, Tool('foo'))
        self.assertRaises(NotOnSquare, b.shoot, None, 4)
        self.assertRaises(NotOnSquare, b.heal, None, 3)
        self.assertRaises(NotOnSquare, b.makeTool, None, None)
        self.assertRaises(NotOnSquare, b.openPortal, 'hey')

        self.assertEqual(b.emit.call_count, 0, str(b.emit.call_args))


    def test_destroyed(self):
        """
        Should return a Deferred which fires when killed.
        """
        bot = self.mkBot()
        d1 = bot.destroyed()
        d2 = bot.destroyed()
        bot.kill()
        self.assertEqual(self.successResultOf(d1), bot)
        self.assertEqual(self.successResultOf(d2), bot)
        self.assertEqual(self.successResultOf(bot.destroyed()), bot)


    def test_kill_energy(self):
        """
        When a bot is killed, any energy they shared should be removed.
        """
        b1 = self.mkBot()
        b2 = self.mkBot()
        b2.square = b1.square

        b1.charge()
        b1.shareEnergy(1, b2)
        b2.emit.reset_mock()

        b1.kill()
        self.assertEqual(b1.generated_energy, None)
        self.assertEqual(b2.energy_pool, [], "Should remove energy from other "
                         "bot's pool")
        b2.emit.assert_called_once_with(Event(b2, 'e.wasted', 1))


    def test_kill_tool(self):
        """
        When a bot is killed, the tool it's using is destroyed.
        """
        b1 = self.mkBot()

        tool = Tool('foo')
        b1.equip(tool)
        b1.kill()
        self.assertEqual(self.successResultOf(tool.destroyed()), tool)


    def test_charge(self):
        """
        A bot can charge, making a new generated_energy which is added to the
        energy_pool.
        """
        b = self.mkBot()
        b.charge()
        self.assertTrue(isinstance(b.generated_energy, Energy),
                        "Should set generated_energy")
        self.assertEqual(b.energy_pool, [b.generated_energy])
        b.emit.assert_any_call(Event(b, 'charged', None))


    def test_charge_tooSoon(self):
        """
        It is an error to try and charge when there's still a generated_energy.
        """
        b = self.mkBot()
        b.charge()
        self.assertRaises(EnergyNotConsumedYet, b.charge)


    def test_charge_energyConsumed(self):
        """
        After energy is consumed, it is okay to charge more.
        """
        b = self.mkBot()
        b.charge()

        # bot consumes it
        b.consumeEnergy(1)
        b.charge()

        # someone else consumes it
        b.generated_energy.consume()
        b.charge()


    def test_canCharge_set_charging_work(self):
        """
        Calling canCharge will set charging_work by asking the square what
        the work is.
        """
        b = self.mkBot()
        b.square.workFor.return_value = Work('foo', 'bar')

        # initial request
        res = self.successResultOf(b.canCharge())
        b.square.workFor.assert_called_once_with(b, 'charge', None)
        self.assertEqual(res, Work('foo', 'bar'), "Should return the Work")
        self.assertEqual(b.charging_work, res)

        # second request before doing the work
        b.square.workFor.reset_mock()
        res = self.successResultOf(b.canCharge())
        self.assertEqual(b.square.workFor.call_count, 0, "Should not have "
                         "gone to the square for the work again")
        self.assertEqual(res, Work('foo', 'bar'), "Should return the Work")

        # charge
        b.charge()
        self.assertEqual(b.charging_work, None, "Should unset charging_work")
        r = b.canCharge()
        self.assertEqual(r.called, False)

        # consume energy to trigger canCharge
        b.consumeEnergy(1)
        b.square.workFor.assert_called_once_with(b, 'charge', None)
        res = self.successResultOf(r)
        self.assertEqual(res, Work('foo', 'bar'))
        self.assertEqual(b.charging_work, res)


    def test_canCharge_sameAnswers(self):
        """
        Asking canCharge should result in the same answer for two callers
        at every stage.
        """
        bot = self.mkBot()
        from uuid import uuid4
        def workFor(*args):
            return uuid4()
        bot.square.workFor.side_effect = workFor

        bot.charge()
        a = bot.canCharge()
        b = bot.canCharge()
        bot.consumeEnergy(1)
        a = self.successResultOf(a)
        b = self.successResultOf(b)
        self.assertEqual(a, b,
                         "canCharge() called while waiting for energy "
                         "consumption should result in same value")
        self.assertEqual(a, bot.charging_work)


    def test_canCharge(self):
        """
        An uncharged bot can charge.
        """
        b = self.mkBot()
        self.assertEqual(b.canCharge().called, True)


    def test_canCharge_waiting(self):
        """
        A charged bot can't charge until the charge has been used.
        """
        b = self.mkBot()
        b.charge()
        d = b.canCharge()
        self.assertEqual(d.called, False)
        b.consumeEnergy(1)
        self.assertEqual(d.called, True)


    def test_receiveEnergies(self):
        """
        A bot can receive energy.
        """
        b = self.mkBot()
        energy = Energy()
        b.receiveEnergies([energy])
        self.assertIn(energy, b.energy_pool, "Bot should know it has it")
        b.emit.assert_called_once_with(Event(b, 'e.received', 1))


    def test_consumeEnergy(self):
        """
        A bot can consume energy in its pool, which will cause the energy to be
        removed from the pool, and an event to be emitted.
        """
        b = self.mkBot()
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
        b = self.mkBot()
        energy = Energy()
        b.receiveEnergies([energy])

        self.assertRaises(NotEnoughEnergy, b.consumeEnergy, 2)
        self.assertEqual(len(b.energy_pool), 1, "Should not remove it")


    def test_shareEnergy(self):
        """
        A bot can share energy with other bots.
        """
        bot1 = self.mkBot()
        bot1.charge()
        e = bot1.generated_energy

        bot2 = self.mkBot()
        bot2.square = bot1.square
        bot2.receiveEnergies = create_autospec(bot2.receiveEnergies)

        bot1.shareEnergy(1, bot2)
        bot2.receiveEnergies.assert_called_once_with([e])
        bot1.emit.assert_any_call(Event(bot1, 'e.shared', bot2))
        self.assertEqual(bot1.energy_pool, [], "Should remove from bot1")


    def test_shareEnergy_notEnough(self):
        """
        An error is raised if you try to share energy that you don't have.
        """
        bot1 = self.mkBot()
        bot1.charge()

        bot2 = self.mkBot()
        bot2.square = bot1.square
        self.assertRaises(NotEnoughEnergy, bot1.shareEnergy, 2, bot2)


    def test_shareEnergy_sameSquare(self):
        """
        A bot can only share energy with another bot on the same square,
        and it can't be a None square.
        """
        bot1 = self.mkBot()
        bot2 = self.mkBot()
        bot2.square = None
        
        self.assertRaises(NotAllowed, bot1.shareEnergy, 1, bot2)

        bot1.square = 'something'
        bot2.square = 'another'
        self.assertRaises(NotAllowed, bot1.shareEnergy, 1, bot2)


    def test_equip(self):
        """
        You can equip a tool.
        """
        bot = self.mkBot()

        tool = Tool('car')
        bot.equip(tool)
        self.assertEqual(bot.tool, tool)
        bot.emit.assert_called_once_with(Event(bot, 'equipped', tool))


    def test_toolDestroyed(self):
        """
        When a tool is destroyed, it is unequipped from the bot.
        """
        bot = self.mkBot()

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
        bot1 = self.mkBot()
        bot2 = self.mkBot()
        bot2.square = bot1.square

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
        bot1 = self.mkBot()
        bot2 = self.mkBot()
        self.assertRaises(LackingTool, bot1.shoot, bot2, 2)

        bot1.tool = Tool('cat')
        self.assertRaises(LackingTool, bot1.shoot, bot2, 2)


    def test_shoot_sameSquare(self):
        """
        You must be on the same square as the thing you're shooting.
        """
        bot1 = self.mkBot()
        bot1.charge()
        bot1.tool = Tool('cannon')
        
        bot2 = self.mkBot()

        self.assertRaises(NotAllowed, bot1.shoot, bot2, 1)


    def test_heal(self):
        """
        You can heal another thing with a repair kit
        """
        bot1 = self.mkBot()
        bot2 = self.mkBot()
        bot2.square = bot1.square

        bot1.equip(Tool('repair kit'))
        bot1.emit.reset_mock()

        bot2.damage(5)
        hp = bot2.hitpoints()

        bot1.heal(bot2, 3)
        self.assertEqual(bot2.hitpoints(), hp+3)
        bot1.emit.assert_called_once_with(Event(bot1, 'healed', bot2))


    def test_heal_noRepairKit(self):
        """
        You can't repair without a repair kit, nor can you do it with a jar of
        mayonnaise.
        """
        bot1 = self.mkBot()
        bot2 = self.mkBot()
        self.assertRaises(LackingTool, bot1.heal, bot2, 2)

        bot1.tool = Tool('jar of mayonnaise')
        self.assertRaises(LackingTool, bot1.heal, bot2, 2)


    def test_heal_sameSquare(self):
        """
        You must be on the same square as the thing you're healing.
        """
        bot1 = self.mkBot()
        bot1.charge()
        bot1.tool = Tool('repair kit')
        
        bot2 = self.mkBot()

        self.assertRaises(NotAllowed, bot1.heal, bot2, 1)


    def test_makeTool(self):
        """
        You can turn ore into a tool.
        """
        b = self.mkBot()
        square = Square(MagicMock())
        square.addThing(b)

        ore = Ore()
        square.addThing(ore)

        b.makeTool(ore, 'yeti')

        # bot
        tool = b.tool
        self.assertTrue(isinstance(tool, Tool))
        self.assertEqual(tool.kind, 'yeti')

        b.emit.assert_any_call(Event(b, 'made', tool))
        
        # lifesource
        ls = square.contents(Lifesource)[0]
        self.assertTrue(isinstance(ls, Lifesource), ls)
        self.assertEqual(ls.other, tool)
        self.assertEqual(tool.lifesource, ls)


    def test_makeTool_sameSquare(self):
        """
        You must be on the same square as the ore to make a tool.
        """
        b = self.mkBot()
        ore = Ore()
        self.assertRaises(NotAllowed, b.makeTool, ore, 'yeti')

        ore.square = 'foo'
        self.assertRaises(NotAllowed, b.makeTool, ore, 'cow')


    def test_openPortal(self):
        """
        You can open a portal by giving it a byte string password.
        """
        bot1 = self.mkBot()
        square = Square(MagicMock())
        square.addThing(bot1)

        ore = Ore()
        square.addThing(ore)

        bot1.makeTool(ore, 'portal')
        ls = square.contents(Lifesource)[0]

        bot1.openPortal('password')
        bot1.emit.assert_any_call(Event(bot1, 'portal.open', None))

        # use Portal
        bot2 = self.mkBot()
        bot2.square = None
        bot2.usePortal(bot1, 'password')
        bot2.emit.assert_any_call(Event(bot2, 'portal.use', bot1))

        self.assertEqual(bot2.square, square, "Should put them in the square")
        self.assertEqual(bot1.tool, None, "Should unequip the portal tool")
        self.assertEqual(ls.other, bot2, "Should pair the Lifesource with "
                         "the new bot")

        # if the first bot is destroyed, it shouldn't affect the new bot
        bot1.kill()
        self.assertEqual(bot2.dead, False)


    def test_openPortal_noPortal(self):
        """
        You can't open a portal without a portal tool.
        """
        bot1 = self.mkBot()
        self.assertRaises(LackingTool, bot1.openPortal, 'hey')

        bot1.tool = Tool('island')
        self.assertRaises(LackingTool, bot1.openPortal, 'ho')


    def test_usePortal_onSquare(self):
        """
        You can't use a portal if you're already in a square.
        """
        bot1 = self.mkBot()
        self.assertRaises(NotAllowed, bot1.usePortal, None, 'anything')


    def test_usePortal_wrongPassword(self):
        """
        If you use the wrong password, you don't get to land.
        """
        bot1 = self.mkBot()
        square = Square(MagicMock())
        square.addThing(bot1)
        
        ore = Ore()
        square.addThing(ore)
        
        bot1.makeTool(ore, 'portal')
        bot1.openPortal('password')

        bot2 = self.mkBot()
        bot2.square = None
        self.assertRaises(NotAllowed, bot2.usePortal, bot1, 'something')


    def test_breakLock(self):
        """
        A bot can break the lock of a Pylon
        """
        bot = self.mkBot(real_square=True)
        pylon = Pylon()
        pylon.setLocks(3)
        bot.square.addThing(pylon)

        bot.breakLock(pylon)
        bot.emit.assert_called_once_with(Event(bot, 'lock.broken', pylon))
        self.assertEqual(pylon.locks, 2)


    def test_breakLock_sameSquare(self):
        """
        A bot has to be in the same square in order to break the lock.
        """
        bot = self.mkBot(real_square=True)
        pylon = Pylon()
        self.assertRaises(NotAllowed, bot.breakLock, pylon)
        pylon.square = 'foo'
        self.assertRaises(NotAllowed, bot.breakLock, pylon)


    def test_breakLock_capture(self):
        """
        A bot that breaks the last lock on a pylon captures the pylon.
        """
        bot = self.mkBot(real_square=True)
        pylon = Pylon()
        pylon.setLocks(1)
        bot.square.addThing(pylon)

        bot.breakLock(pylon)
        bot.emit.assert_any_call(Event(bot, 'pylon.captured', pylon))
        self.assertEqual(pylon.team, bot.team, "Should change team")
        self.assertEqual(pylon.locks, 1, "Should have another lock")


    def test_addLock(self):
        """
        A bot can add a lock to a Pylon
        """
        bot = self.mkBot(real_square=True)
        pylon = Pylon()
        pylon.setLocks(3)
        bot.square.addThing(pylon)

        bot.addLock(pylon)
        bot.emit.assert_called_once_with(Event(bot, 'lock.added', pylon))
        self.assertEqual(pylon.locks, 4)


    def test_addLock_sameSquare(self):
        """
        A bot has to be in the same square in order to add a lock.
        """
        bot = self.mkBot(real_square=True)
        pylon = Pylon()
        self.assertRaises(NotAllowed, bot.addLock, pylon)
        pylon.square = 'foo'
        self.assertRaises(NotAllowed, bot.addLock, pylon)




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


