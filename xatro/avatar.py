


class Avatar(object):
    """
    I am the client-controllable interface for a game piece in the world.

    Write your protocols to use my public methods.
    """

    _game_piece = None
    _world = None

    def __init__(self, world=None):
        self._world = world


    def availableCommands(self):
        return []