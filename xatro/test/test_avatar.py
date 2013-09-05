from twisted.trial.unittest import TestCase


from xatro.avatar import Avatar


class AvatarTest(TestCase):


    def test_availableCommands(self):
        """
        An avatar has a list of available command classes.
        """
        a = Avatar()
        self.assertEqual(a.availableCommands(), [])


    def test_game_piece(self):
        """
        An avatar has a game piece.
        """
        a = Avatar()
        self.assertEqual(a._game_piece, None)


    def test_world(self):
        """
        An avatar knows about the world.
        """
        a = Avatar('foo')
        self.assertEqual(a._world, 'foo')
