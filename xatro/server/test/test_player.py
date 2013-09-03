from twisted.trial.unittest import TestCase
from zope.interface.verify import verifyObject

from mock import MagicMock, create_autospec

from xatro.test.test_work import findResult
from xatro.work import WorkMaker
from xatro.server.board import Bot
from xatro.server.board import NotAllowed, NotEnoughEnergy
from xatro.server.player import BotPlayer
from xatro.server.interface import IEventReceiver



class BotPlayerTest(TestCase):


    def test_init(self):
        """
        A bot player has rules and an event_receiver
        """
        receiver = MagicMock()
        player = BotPlayer(receiver)
        self.assertEqual(player._bot, None)
        self.assertEqual(player._rules, None)
        self.assertEqual(player._board, None)
        self.assertEqual(player._event_receiver, receiver)


    def test_IEventReceiver(self):
        verifyObject(IEventReceiver, BotPlayer(None))


    def test_eventReceived(self):
        """
        I send events to my event_receiver
        """
        called = []
        player = BotPlayer(called.append)
        player.eventReceived('foo')
        self.assertEqual(called, ['foo'])


    def test_makeBot(self):
        """
        I make a bot that sends notifications to me.
        """
        called = []
        player = BotPlayer(called.append)
        player.makeBot('team', 'name')
        self.assertTrue(isinstance(player._bot, Bot))
        self.assertEqual(player._bot.team, 'team')
        self.assertEqual(player._bot.name, 'name')

        player._bot.eventReceived('hey')
        self.assertEqual(called, ['hey'], "Notifications received by the "
                         "bot should be received by the player")


    def test_makeBot_twice(self):
        """
        It is an error to make the bot twice.
        """
        player = BotPlayer(None)
        player.makeBot('hey', 'go')
        self.assertRaises(NotAllowed, player.makeBot, 'hoo', 'ha')


    def test_joinBoard(self):
        """
        You can join a board.
        """
        player = BotPlayer(None)
        player.makeBot('hey', 'ho')

        board = MagicMock()
        board.rules = 'hey'
        player.joinBoard(board)
        
        board.addBot.assert_called_once_with(player._bot)
        self.assertEqual(player._board, board)
        self.assertEqual(player._rules, 'hey')


    def test_allowed_functions(self):
        """
        These functions can be called by the users of the PlayerBot.

        This seems like kind of a silly test.
        """
        expected = [
            'kill',
            'hitpoints',
            'charge',
            'canCharge',
            'shareEnergy',
            'shoot',
            'heal',
            'openPortal',
            'usePortal',
            'makeTool',
            'breakLock',
            'addLock',
            'move',
            'look',
        ]
        player = BotPlayer(None)
        self.assertEqual(set(expected), set(player._allowed_functions))


    def readyPlayer(self):
        player = BotPlayer(None)
        player.makeBot('hey', 'ho')
        player._bot.square = MagicMock()

        board = MagicMock()
        board.rules = MagicMock()
        player.joinBoard(board)
        return player


    def test_callOnBot_functionNotAllowed(self):
        """
        If a function is not allowed to be called on a bot, raise NotAllowed
        """
        player = self.readyPlayer()
        self.assertRaises(NotAllowed, player.callOnBot, None, 'foo')


    def test_callOnBot(self):
        """
        callBot will call a function on the bot if there's no work requirement
        of energy requirement.
        """
        player = self.readyPlayer()
        rules = player._rules

        # no energy required
        rules.energyRequirement.return_value = 0

        # no work required
        rules.workRequirement.return_value = None

        player._bot.foo = MagicMock(return_value='foo result')
        player._allowed_functions.append('foo')

        r = player.callOnBot(None, 'foo', 'arg1', 'arg2')
        rules.workRequirement.assert_called_once_with(
                player._bot, 'foo', 'arg1', 'arg2')
        self.assertEqual(rules.assertSolution.call_count, 0)
        rules.energyRequirement.assert_called_once_with(
                player._bot, 'foo', 'arg1', 'arg2')
        player._bot.foo.assert_called_once_with('arg1', 'arg2')
        self.assertEqual(r, 'foo result')


    def test_callOnBot_energyRequirement(self):
        """
        If the function has an energy requirement, consume that energy before
        calling the function.
        """
        player = self.readyPlayer()
        rules = player._rules

        # energy required
        rules.energyRequirement.return_value = 2

        # no work required
        rules.workRequirement.return_value = None

        player._bot.consumeEnergy = create_autospec(player._bot.consumeEnergy)
        player._bot.foo = MagicMock(return_value='foo result')
        player._allowed_functions.append('foo')

        r = player.callOnBot(None, 'foo', 'arg1', 'arg2')
        player._bot.consumeEnergy.assert_called_once_with(2)
        player._bot.foo.assert_called_once_with('arg1', 'arg2')
        self.assertEqual(r, 'foo result')


    def test_callOnBot_notEnoughEnergy(self):
        """
        If the function requires energy and the bot doesn't have enough, don't
        call the function and raise an error.
        """
        player = self.readyPlayer()
        rules = player._rules

        # energy required
        rules.energyRequirement.return_value = 2

        # no work required
        rules.workRequirement.return_value = None

        player._bot.consumeEnergy = create_autospec(player._bot.consumeEnergy,
                                    side_effect=NotEnoughEnergy)
        player._bot.foo = MagicMock(return_value='foo result')
        player._allowed_functions.append('foo')

        self.assertRaises(NotEnoughEnergy, player.callOnBot, None, 'foo', 'arg')
        player._bot.consumeEnergy.assert_called_once_with(2)
        self.assertEqual(player._bot.foo.call_count, 0)


    def test_callOnBot_workRequirement(self):
        """
        If work is required, and a valid solution is presented, then allow
        the operation to proceed.
        """
        player = self.readyPlayer()
        rules = player._rules

        maker = WorkMaker()
        work = maker.getWork()
        solution = findResult(work.nonce, work.goal)

        # no energy required
        rules.energyRequirement.return_value = 0

        # work required
        rules.workRequirement.return_value = work

        player._bot.foo = MagicMock(return_value='foo result')
        player._allowed_functions.append('foo')

        r = player.callOnBot(solution, 'foo', 'arg1')
        rules.assertSolution.assert_called_once_with(solution, work)
        player._bot.foo.assert_called_once_with('arg1')
        self.assertEqual(r, 'foo result')








