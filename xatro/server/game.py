

class Game(object):
    """
    I am a game running on a Board.
    """

    state = 'init'


    def __init__(self, board=None, event_receiver=None):
        self.board = board
        self.event_receiver = event_receiver

