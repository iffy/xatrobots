"""
Board and Square and such.
"""


class Square(object):
    """
    I am a square on the gameboard.
    """

    board = None
    pylon = None


    def __init__(self):
        self.bots = {}
        self.materials = {}



class Pylon(object):
    """
    I am a pylon within a square.
    """

    team = None
    work = None

    def __init__(self, locks):
        self.locks = locks