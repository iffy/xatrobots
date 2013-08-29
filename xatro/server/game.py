class Game(object):
    """
    I am a game running on a Board.
    """

    state = 'init'


    def __init__(self, board, event_receiver):
        self.board = board
        self.event_receiver = event_receiver