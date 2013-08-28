"""
Board and Square and such.
"""


class Square(object):
    """
    I am a square on the gameboard.

    @ivar board: L{Board} instance.
    @ivar pylon: L{Pylon} instance.
    @ivar bots: Dictionary of bots in this square.
    @ivar materials: Dictionary of materials in this square.
    """

    board = None
    pylon = None


    def __init__(self):
        self.bots = {}
        self.materials = {}



class Pylon(object):
    """
    I am a pylon within a square.

    @ivar team: Team name that owns me
    @type team: str

    @ivar work: The L{Work} required to unlock the next lock.
    """

    team = None
    work = None

    def __init__(self, locks):
        self.locks = locks



class Material(object):
    """
    I am a material.

    @ivar health: If an integer, the current health of the material.
    @ivar current_use: C{None} if not in use, otherwise this is the object
        I've been provisioned into.
    """

    health = None
    current_use = None