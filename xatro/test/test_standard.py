from twisted.trial.unittest import TestCase
from twisted.internet import defer
from zope.interface.verify import verifyObject

from mock import MagicMock

from xatro import action
from xatro.auth import MemoryStoredPasswords
from xatro.world import World
from xatro.error import NotAllowed
from xatro.engine import XatroEngine
from xatro.interface import IXatroEngine
from xatro.standard import StandardRules



class StandardRulesTest(TestCase):


    def worldAndRules(self):
        """
        Get a fresh world and set of rules.
        """
        auth = MemoryStoredPasswords()
        rules = StandardRules()
        engine = XatroEngine(rules)
        world = World(MagicMock(), engine, auth)
        return world, rules


    def test_IXatroEngine(self):
        verifyObject(IXatroEngine, StandardRules())


    def test_onlyBotsCanExecute(self):
        """
        Only bots can execute commands.
        """
        world = World(MagicMock())
        rules = StandardRules()

        bot = world.create('bot')['id']
        rules.isAllowed(world, action.ListSquares(bot))

        nonbot = world.create('foo')['id']
        self.assertRaises(NotAllowed, rules.isAllowed, world,
                          action.ListSquares(nonbot))


    def test_energyRequirement_default(self):
        """
        Most things require 0 energy
        """
        world = World(MagicMock())
        rules = StandardRules()

        self.assertEqual(rules.energyRequirement(world,
                         action.ListSquares('foo')), 0)


    def test_energyRequirement_required(self):
        """
        Various actions require the following amounts of energy.
        """
        world = World(MagicMock())
        rules = StandardRules()
        expectations = [
            (0, action.Look('foo')),
            (0, action.Charge('foo')),
            (0, action.ShareEnergy('foo', 'bar', 3)),
            (0, action.ConsumeEnergy('foo', 2)),
            (1, action.MakeTool('foo', 'ore', 'tool')),
            (1, action.OpenPortal('foo', 'ore', 'user')),
            (0, action.UsePortal('foo', 'portal')),
            (0, action.ListSquares('foo')),
            (2, action.AddLock('foo', 'target')),
            (2, action.BreakLock('foo', 'target')),
        ]
        for energy, cmd in expectations:
            self.assertEqual(rules.energyRequirement(world, cmd), energy,
                             "Expected command %r to require %r energy" % (
                             cmd, energy))


    def test_energyRequirement_Shoot(self):
        """
        Shooting energy proportional to damage (with some bonus for more energy)
        """
        world = World(MagicMock())
        rules = StandardRules()
        expectations = [
            # hp, energy
            (1, 1),
            (2, 2),
            (3, 2),
            (4, 3),
            (5, 3),
            (6, 3),
        ]
        for hp, energy in expectations:
            actual = rules.energyRequirement(world,
                                             action.Shoot('foo', 'bar', hp))
            self.assertEqual(actual, energy,
                             "Expected shooting for %r to take %r energy, not "
                             "%r energy" % (hp, energy, actual))


    def test_energyRequirement_Repair(self):
        """
        Repairing energy proportional to hp (with some bonus for more energy)
        """
        world = World(MagicMock())
        rules = StandardRules()
        expectations = [
            # hp, energy
            (1, 1),
            (2, 2),
            (3, 2),
            (4, 3),
            (5, 3),
            (6, 3),
        ]
        for hp, energy in expectations:
            actual = rules.energyRequirement(world,
                                             action.Repair('foo', 'bar', hp))
            self.assertEqual(actual, energy,
                             "Expected repairing for %r to take %r energy, not "
                             "%r energy" % (hp, energy, actual))


    def test_failIfNotOnBoard(self):
        """
        The following actions require a bot to be on the board.
        """
        world = World(MagicMock())
        rules = StandardRules()

        bot = world.create('bot')['id']

        actions = [
            action.Charge(bot),
            action.ShareEnergy(bot, 'foo', 2),
            action.ConsumeEnergy(bot, 2),
            action.Shoot(bot, 'foo', 1),
            action.Repair(bot, 'foo', 1),
            action.MakeTool(bot, 'foo', 'foo'),
            action.OpenPortal(bot, 'foo', 'foo'),
            action.AddLock(bot, 'foo'),
            action.BreakLock(bot, 'foo'),
        ]

        for a in actions:
            try:
                rules.isAllowed(world, a)
            except NotAllowed:
                pass
            else:
                self.fail("You must be on a square to do %r" % (a,))


    def test_failIfOnBoard(self):
        """
        The following actions may only be done when NOT on a board.
        """
        world = World(MagicMock())
        rules = StandardRules()

        bot = world.create('bot')['id']
        square = world.create('square')['id']
        action.Move(bot, square).execute(world)

        actions = [
            action.UsePortal(bot, 'foo'),
            action.JoinTeam(bot, 'team', 'foo'),
            action.CreateTeam(bot, 'team', 'foo'),
        ]

        for a in actions:
            try:
                rules.isAllowed(world, a)
            except NotAllowed:
                pass
            else:
                self.fail("You must be off of a square to do %r" % (a,))


    @defer.inlineCallbacks
    def test_oneBotCanLandWithoutPortal(self):
        """
        A bot that's part of a team can move onto a square.
        """
        # create a bot that's on a team
        world, rules = self.worldAndRules()

        bot = world.create('bot')['id']
        yield world.execute(action.CreateTeam(bot, 'ATeam', 'password'))
        yield world.execute(action.JoinTeam(bot, 'ATeam', 'password'))

        # it's okay to land on a square.
        square = world.create('square')['id']
        rules.isAllowed(world, action.Move(bot, square))
        self.assertEqual(rules.energyRequirement(world,
                         action.Move(bot, square)), 0,
                         "It should not take energy to move the bot on to "
                         "the square because he can't charge when on deck.")
        # by getting here, it didn't fail


    @defer.inlineCallbacks
    def test_onlyOneBotPerTeamCanLandWithoutPortal(self):
        """
        If one bot on a team is already on the board, other bots are not
        allowed to go on the board by moving.
        """
        # create a non-fake world
        world, rules = self.worldAndRules()

        # create a bot that's on a team
        bot = world.create('bot')['id']
        yield world.execute(action.CreateTeam(bot, 'ATeam', 'password'))
        yield world.execute(action.JoinTeam(bot, 'ATeam', 'password'))

        # land the bot on a square.
        square = world.create('square')['id']
        rules.isAllowed(world, action.Move(bot, square))
        yield world.execute(action.Move(bot, square))

        # create another bot on the same team
        bot2 = world.create('bot')['id']
        yield action.JoinTeam(bot2, 'ATeam', 'password').execute(world)

        # it should not be allowed to land the bot on a square until the other
        # bot dies.
        yield self.assertFailure(world.execute(action.Move(bot2, square)),
                                  NotAllowed)

        # bot1 is destroyed, now bot2 can land
        yield world.destroy(bot)
        yield world.execute(action.Move(bot2, square))


    def test_mustHaveTeamToLandWithoutPortal(self):
        """
        A bot must be a member of a team to move from the deck onto the board.
        """
        world, rules = self.worldAndRules()

        bot = world.create('bot')['id']

        square = world.create('square')['id']
        self.assertRaises(NotAllowed, rules.isAllowed, world,
                          action.Move(bot, square))


    def test_mustHaveTeamToUsePortal(self):
        """
        A bot that's not a member of a team can not use a portal.
        """
        world, rules = self.worldAndRules()

        bot = world.create('bot')['id']
        portal = world.create('portal')['id']

        self.assertRaises(NotAllowed, rules.isAllowed, world,
                          action.UsePortal(bot, portal))


    def equippedBotWithViableTarget(self, tool):
        """
        Create a scenario in which shooting is allowed.
        """
        world, rules = self.worldAndRules()

        # make square and ore
        square = world.create('square')['id']
        ore = world.create('ore')['id']
        action.Move(ore, square).execute(world)

        # equip bot
        bot = world.create('bot')['id']
        action.Move(bot, square).execute(world)
        action.MakeTool(bot, ore, tool).execute(world)

        # make target
        target = world.create('bot')['id']
        world.setAttr(target, 'hp', 10)
        action.Move(target, square).execute(world)

        self.world = world
        self.rules = rules
        self.square = square
        self.bot = bot
        self.target = target
        return self.bot


    def test_isAllowed_Shoot(self):
        """
        You are allowed to shoot if you are on the same square and have a
        cannon.
        """
        bot = self.equippedBotWithViableTarget('cannon')

        # shooting is allowed
        self.rules.isAllowed(self.world, action.Shoot(self.bot, self.target, 1))


    def test_Shoot_mustBeOnSameSquare(self):
        """
        A bot must be on the same square as the target it is shooting.
        """
        bot = self.equippedBotWithViableTarget('cannon')

        square2 = self.world.create('square')['id']
        action.Move(self.target, square2).execute(self.world)

        self.assertRaises(NotAllowed, self.rules.isAllowed, self.world,
                          action.Shoot(self.bot, self.target, 1))


    def test_Shoot_mustHaveCannon(self):
        """
        A bot must have a cannon in order to shoot.
        """
        bot = self.equippedBotWithViableTarget('wrench')

        self.assertRaises(NotAllowed, self.rules.isAllowed, self.world,
                          action.Shoot(self.bot, self.target, 1))


    def test_Shoot_targetMustBeVulnerable(self):
        """
        You can only shoot things that are vulnerable
        """
        bot = self.equippedBotWithViableTarget('cannon')

        invulnerable = self.world.create('ore')['id']
        action.Move(invulnerable, self.square).execute(self.world)

        self.assertRaises(NotAllowed, self.rules.isAllowed, self.world,
                          action.Shoot(self.bot, invulnerable, 1))


    def test_isAllowed_Repair(self):
        """
        You are allowed to Repair if you are on the same square and have a
        wrench.
        """
        bot = self.equippedBotWithViableTarget('wrench')

        # Repairing is allowed
        self.rules.isAllowed(self.world, action.Repair(self.bot, self.target, 1))


    def test_Repair_mustBeOnSameSquare(self):
        """
        A bot must be on the same square as the target it is Repairing.
        """
        bot = self.equippedBotWithViableTarget('wrench')

        square2 = self.world.create('square')['id']
        action.Move(self.target, square2).execute(self.world)

        self.assertRaises(NotAllowed, self.rules.isAllowed, self.world,
                          action.Repair(self.bot, self.target, 1))


    def test_Repair_mustHaveWrench(self):
        """
        A bot must have a wrench in order to Repair.
        """
        bot = self.equippedBotWithViableTarget('cannon')

        self.assertRaises(NotAllowed, self.rules.isAllowed, self.world,
                          action.Repair(self.bot, self.target, 1))


    def test_Repair_targetMustBeVulnerable(self):
        """
        You can only Repair things that are vulnerable
        """
        bot = self.equippedBotWithViableTarget('wrench')

        invulnerable = self.world.create('ore')['id']
        action.Move(invulnerable, self.square).execute(self.world)

        self.assertRaises(NotAllowed, self.rules.isAllowed, self.world,
                          action.Repair(self.bot, invulnerable, 1))


    def test_MakeTool(self):
        """
        You can make a tool
        """
        world, rules = self.worldAndRules()

        # make square and ore
        square = world.create('square')['id']
        ore = world.create('ore')['id']
        action.Move(ore, square).execute(world)

        # make bot
        bot = world.create('bot')['id']
        action.Move(bot, square).execute(world)

        rules.isAllowed(world, action.MakeTool(bot, ore, 'cannon'))


    def test_MakeTool_oreOnly(self):
        """
        You can only make a tool out of ore
        """
        world, rules = self.worldAndRules()

        # make square and ore
        square = world.create('square')['id']
        otherbot = world.create('bot')['id']
        action.Move(otherbot, square).execute(world)

        # make bot
        bot = world.create('bot')['id']
        action.Move(bot, square).execute(world)

        self.assertRaises(NotAllowed, rules.isAllowed, world,
                          action.MakeTool(bot, otherbot, 'cannon'))


    def test_MakeTool_sameSquare(self):
        """
        You can only make a tool out of a piece of ore in the same square.
        """
        world, rules = self.worldAndRules()

        # make square and ore
        square = world.create('square')['id']
        ore = world.create('ore')['id']
        action.Move(ore, square).execute(world)

        # make bot in different square
        square2 = world.create('square')['id']
        bot = world.create('bot')['id']
        action.Move(bot, square2).execute(world)

        self.assertRaises(NotAllowed, rules.isAllowed, world,
                          action.MakeTool(bot, ore, 'cannon'))


    def test_workRequirement(self):
        self.fail('write me')









