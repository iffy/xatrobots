from twisted.trial.unittest import TestCase


from xatro.server.game import Game



class GameTest(TestCase):


    def test_attributes(self):
        """
        A game should have a board and an event receiver.
        """
        game = Game('board', 'event_receiver')
        self.assertEqual(game.board, 'board')
        self.assertEqual(game.event_receiver, 'event_receiver')
        self.assertEqual(game.state, 'init')
