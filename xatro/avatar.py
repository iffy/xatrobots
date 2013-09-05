from xatro.error import NotAllowed



class Avatar(object):
    """
    I am the client-controllable interface for a game piece in the world.

    Write your protocols to use my public methods.
    """

    _game_piece = None
    _world = None

    def __init__(self, world=None):
        self._world = world
        self._available_commands = []
        self._pending_events = []
        self._eventReceived = self._pending_events.append


    def setGamePiece(self, game_piece):
        """
        XXX
        """
        if self._game_piece:
            raise NotAllowed('You may not change the game piece you control')
        self._game_piece = game_piece
        self._world.receiveFor(self._game_piece, self.eventReceived)


    def quit(self):
        """
        Quit from the game/world/server.
        """
        self._world.destroy(self._game_piece)


    def eventReceived(self, event):
        """
        An event from the game/world is received.
        """
        self._eventReceived(event)


    def setEventReceiver(self, receiver):
        """
        Register a function to receive all the events received by me (which are
        really just the events received by my game piece).
        
        All previously-received events will be given to C{receiver} immediately.
        """
        while self._pending_events:
            receiver(self._pending_events.pop(0))
        self._eventReceived = receiver


    def availableCommands(self):
        """
        XXX
        """
        return self._available_commands


    def makeCommand(self, command_cls, *args, **kwargs):
        """
        XXX
        """
        return command_cls(self._game_piece, *args, **kwargs)


    def execute(self, command_cls, *args, **kwargs):
        """
        Execute a command with the given parameters.  The command's first
        argument will always by my game piece.
        """
        cmd = self.makeCommand(command_cls, *args, **kwargs)
        return self._world.execute(cmd)