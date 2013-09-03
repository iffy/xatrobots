from twisted.trial.unittest import TestCase
from zope.interface.verify import verifyObject

from mock import MagicMock, create_autospec

from xatro.server.event import Event
from xatro.server.game import Game, StaticRules
from xatro.server.board import Bot, Pylon
from xatro.server.interface import IGameRules, IEventReceiver
from xatro.work import WorkMaker, Work, InvalidSolution
from xatro.test.test_work import findResult



class GameTest(TestCase):


    def test_IEventReceiver(self):
        verifyObject(IEventReceiver, Game())


    def test_subscribeAndUnsubscribe(self):
        """
        You can subscribe a function to be called when events happen.
        """
        game = Game()
        c1 = []
        c2 = []
        game.subscribe(c1.append)
        game.subscribe(c2.append)

        game.eventReceived('foo')
        self.assertEqual(c1, ['foo'])
        self.assertEqual(c2, ['foo'])
        
        game.unsubscribe(c1.append)
        game.eventReceived('bar')
        self.assertEqual(c1, ['foo'])
        self.assertEqual(c2, ['foo', 'bar'])


    def test_errorInSubscriber(self):
        """
        An error in a subscriber will not prevent other subscribers from
        getting the message
        """
        game = Game()
        called = []
        game.subscribe('not a function')
        game.subscribe(called.append)

        game.eventReceived('foo')
        self.assertEqual(called, ['foo'])



class StaticRulesTest(TestCase):


    def test_IGameRules(self):
        verifyObject(IGameRules, StaticRules())


    def test_assertSolution_good(self):
        """
        A good solution won't cause a problem.
        """
        rules = StaticRules()

        maker = WorkMaker()
        work = maker.getWork()
        
        result = findResult(work.nonce, work.goal)
        rules.assertSolution(result, work)


    def test_assertSolution_bad(self):
        """
        A bad solution will raise an exception.
        """
        rules = StaticRules()

        maker = WorkMaker()
        work = maker.getWork()
        self.assertRaises(InvalidSolution, rules.assertSolution, '', work)
        self.assertRaises(InvalidSolution, rules.assertSolution, None, work)


    def test_energyRequirement_default(self):
        """
        The default_energy_requirement attribute should determine the energy
        required to perform tasks.
        """
        rules = StaticRules()
        self.assertEqual(rules.default_energy_requirement, 0)

        rules.default_energy_requirement = 7
        self.assertEqual(rules.energyRequirement(None, 'foo'), 7)


    def test_energyRequirement_override(self):
        """
        You can override the energy requirement for various actions.
        """
        rules = StaticRules()
        rules.energy_requirements['ski'] = 12
        self.assertEqual(rules.energyRequirement(None, 'ski'), 12)
        self.assertEqual(rules.energyRequirement(None, 'swim'), 0)


    def test_energyRequirements(self):
        """
        The following actions should require the following amount of energy.
        """
        rules = StaticRules()
        expectations = [
            ('makeTool', 1),
            ('openPortal', 1),
            ('breakLock', 3),
            ('addLock', 3),
            ('move', 2),
        ]
        for action, expected_energy in expectations:
            actual = rules.energyRequirement(None, action)
            self.assertEqual(actual, expected_energy,
                             "%r should require %r, not %r" % (action,
                             expected_energy, actual))


    def test_eventReceived(self):
        """
        Unknown events are ignored.
        """
        rules = StaticRules()
        rules.eventReceived(Event('foo', 'bar', 'baz'))


    def test_eventReceived_pylon_captured(self):
        """
        When a pylon is captured, locks should be applied.
        """
        pylon = Pylon()

        rules = StaticRules()
        rules.locks_after_capture = 8

        rules.eventReceived(Event('bot', 'pylon_captured', pylon))

        self.assertEqual(pylon.locks, 8)


    def test_eventReceived_lock_broken(self):
        """
        When a lock is broken, work efforts should be changed.
        """
        pylon = Pylon()
        self.assertEventCausesPylonWorkToChange(pylon,
            Event('bot', 'lock_broken', pylon))


    def test_eventReceived_lock_added(self):
        """
        When a lock is added to a pylon, the work efforts should be changed.
        """
        pylon = Pylon()
        self.assertEventCausesPylonWorkToChange(pylon,
            Event('bot', 'lock_added', pylon))


    def test_eventReceived_pylon_entered(self):
        """
        When a pylon is placed on a square, locks should be applied.
        """
        pylon = Pylon()

        rules = StaticRules()
        rules.starting_locks = 8

        rules.eventReceived(Event(pylon, 'entered', 'square'))

        self.assertEqual(pylon.locks, 8)


    def test_eventReceived_pylon_locks(self):
        """
        When the number of locks on a pylon changes, the work efforts should
        be adjusted.
        """
        pylon = Pylon()
        self.assertEventCausesPylonWorkToChange(pylon,
            Event(pylon, 'pylon_locks', 4))


    def assertEventCausesPylonWorkToChange(self, pylon, event):
        """
        Assert that the given event will cause pylon work efforts to change.
        """
        pylon.setLockWork = create_autospec(pylon.setLockWork)
        pylon.setBreakLockWork = create_autospec(pylon.setBreakLockWork)

        rules = StaticRules()

        # so we can tell a difference between these otherwise identical
        # objects, we'll set some goofy values.
        rules.breakLock_work_maker.scale = 9
        rules.addLock_work_maker.scale = 9000

        rules.eventReceived(event)

        self.assertEqual(pylon.setLockWork.call_count, 1)
        self.assertEqual(pylon.setBreakLockWork.call_count, 1)

        self.assertEqual(pylon.setLockWork.call_args[0][0].goal,
                         rules.addLock_work_maker.getWork().goal,
                         "Should set it to work as returned by the correct "
                         "work maker")
        self.assertEqual(pylon.setBreakLockWork.call_args[0][0].goal,
                         rules.breakLock_work_maker.getWork().goal,
                         "Should set it to work as returned by the correct "
                         "work maker")


    def test_eventReceived_bot_joined(self):
        """
        When a bot joins the game give them hitpoints.
        """
        bot = Bot('foo', 'bar')

        bot.setHitpoints = create_autospec(bot.setHitpoints, wraps=True)

        rules = StaticRules()
        rules.bot_hitpoints = 30
        rules.eventReceived(Event(bot, 'joined', None))
        bot.setHitpoints.assert_called_once_with(30)


    def test_eventReceived_e_gone(self):
        """
        When a bot's energy is gone, give them new charging_work.
        """
        bot = Bot('foo', 'bar')

        rules = StaticRules()
        rules.charge_work_maker.scale = 89

        rules.eventReceived(Event(bot, 'e_gone', None))
        self.assertTrue(isinstance(bot.charging_work, Work), "Should set "
                        "charging_work to Work")
        self.assertEqual(bot.charging_work.goal,
                         rules.charge_work_maker.getWork().goal)


    def test_energyToHitpoints(self):
        """
        Energy to hitpoints should follow this scale
        """
        expectations = [
            # (energy, hp)
            (1, 1),
            (2, 3),
            (3, 6),
        ]
        rules = StaticRules()
        for e, hp in expectations:
            actual = rules.energyToHitpoints('bot', 'foo', 'target', e)
            self.assertEqual(actual, hp,
                             "Expected %r energy -> %r hp, not %r hp" % (
                             e, hp, actual))


    def test_energyToHitpoints_override(self):
        """
        You can override the energyToHitpoint conversion
        """
        rules = StaticRules()
        rules.default_energy_to_hp[2] = 27
        self.assertEqual(rules.energyToHitpoints(None, 'heal', None, 2), 27)


    def test_energyToHitpoints_errors(self):
        """
        You may not use more than 3 energy to shoot or heal
        """
        rules = StaticRules()
        self.assertRaises(Exception, rules.energyToHitpoints, 'bot', 'action',
                          'target', 4)
        self.assertRaises(Exception, rules.energyToHitpoints, 'bot', 'action',
                          'target', -1)
        self.assertRaises(Exception, rules.energyToHitpoints, 'bot', 'action',
                          'target', 0)


    def test_energyToHitpoints_heal_different_than_shoot(self):
        """
        You can make heal and shoot have different energy-to-hitpoint
        conversions
        """
        rules = StaticRules()
        rules.energy_to_hp['heal'][7] = 29
        rules.energy_to_hp['shoot'][7] = 90
        self.assertEqual(rules.energyToHitpoints(None, 'heal', None, 7), 29)
        self.assertEqual(rules.energyToHitpoints(None, 'heal', None, 1), 1)
        self.assertEqual(rules.energyToHitpoints(None, 'shoot', None, 7), 90)
        self.assertEqual(rules.energyToHitpoints(None, 'shoot', None, 2), 3)


    def test_workRequirement_None_byDefault(self):
        """
        By default, things don't take work.
        """
        rules = StaticRules()
        self.assertEqual(rules.workRequirement(None, 'shave', 'yeti'), None)


    def test_workRequirement_charge(self):
        """
        Charging requires the work set on the bot.
        """
        rules = StaticRules()
        
        bot = Bot('foo', 'bar')
        bot.charging_work = 'foo'
        work = rules.workRequirement(bot, 'charge')
        self.assertEqual(work, 'foo', "Should use the value set on the bot")


    def test_workRequirement_addLock(self):
        """
        Locking requires the work set on the Pylon
        """
        rules = StaticRules()

        pylon = Pylon()
        pylon.tolock = 'hey'
        work = rules.workRequirement(MagicMock(), 'addLock', pylon)
        self.assertEqual(work, 'hey', "Should use the pylon.tolock attribute")


    def test_workRequirement_breakLock(self):
        """
        Breaking locks requires work
        """
        rules = StaticRules()
        
        pylon = Pylon()
        pylon.tobreak = 'foo'
        work = rules.workRequirement(MagicMock(), 'breakLock', pylon)
        self.assertEqual(work, 'foo', "Should use the pylon.tobreak attr")


    def test_isAllowed_default(self):
        """
        Everything is allowed by default.
        """
        rules = StaticRules()
        rules.isAllowed('foo', 'bar')




