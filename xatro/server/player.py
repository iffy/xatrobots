
from zope.interface import implements
from xatro.server.interface import IEventReceiver
from xatro.server.board import Bot, NotAllowed



class BotPlayer(object):
    """
    I am a player.  Unlike the L{xatro.server.board.Bot} object whose public
    interface lets you cheat, I follow all the rules.  I am the thing you
    should write network-facing server protocols to use.
    """

    implements(IEventReceiver)

    _bot = None
    _board = None
    _rules = None
    _event_receiver = None


    def __init__(self, event_receiver):
        """
        @param event_receiver: A function that will be called with every
            event I receive.
        """
        self._event_receiver = event_receiver
        self._allowed_functions = [
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


    def eventReceived(self, event):
        """
        Pass the event on to my C{event_receiver}.
        """
        self._event_receiver(event)


    def makeBot(self, team, name):
        """
        Create my Bot
        """
        if self._bot:
            raise NotAllowed("You already made a bot")
        self._bot = Bot(team, name, self.eventReceived)


    def joinBoard(self, board):
        """
        Join a game board and acquire the rules to follow.
        """
        board.addBot(self._bot)
        self._board = board
        self._rules = board.rules


    def callOnBot(self, work_solution, func, *args, **kwargs):
        """
        Call a function on the bot.

        @param work_solution: A bytestring solution to the work needed to call
            this function or C{None} if no work is required.

        @param func: Name of the function on the L{Bot} to call.
        @param *args: Arguments to pass to function
        @param **kwargs: Keyword arguments to pass to the function.

        @raise NotAllowed: If the function isn't one of the allowed functions.

        @raise InvalidSolution: If the C{work_solution} provided does not
            satisfy the work requirement (if there is a work requirement).
        
        @raise NotEnoughEnergy: If the operation requires more energy than
            the bot has.

        @return: The result of the function
        """
        if func not in self._allowed_functions:
            raise NotAllowed(func)

        # work requirement
        work = self._rules.workRequirement(self._bot, func, *args, **kwargs)
        if work:
            self._rules.assertSolution(work_solution, work)

        # energy requirement
        energy = self._rules.energyRequirement(self._bot, func, *args, **kwargs)
        self._bot.consumeEnergy(energy)

        return getattr(self._bot, func)(*args, **kwargs)


