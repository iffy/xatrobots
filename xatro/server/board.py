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

    @ivar unlock_work: The L{Work} required to unlock the next lock.
    @ivar lock_work: The L{Work} required to add another lock.
    """

    team = None
    unlock_work = None
    lock_work = None

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



class Bot(object):
    """
    I am a bot in play.

    @ivar team: Team name
    @ivar name: Bot name
    @ivar health: Amount of health left. 0 = dead.
    @ivar equipment: Any piece of equipment I have.
    @ivar portal: The portal where I landed.
    @ivar square: The square I'm in right now.
    """

    team = None
    name = None
    health = 10
    equipment = None
    portal = None
    square = None


    def __init__(self, team, name):
        self.team = team
        self.name = name
        self.energy = []



class Energy(object):
    """
    I am energy.  ooowwaaoooohhhh

    @ivar bot: The L{Bot} that produced me.
    """

    def __init__(self, bot):
        self.bot = bot


