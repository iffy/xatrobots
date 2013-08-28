from twisted.trial.unittest import TestCase


from xatro.server.board import Square, Pylon


class SquareTest(TestCase):


    def test_attributes(self):
        """
        A Square should have bots, materials, a pylon and a board.
        """
        q = Square()
        self.assertEqual(q.board, None)
        self.assertEqual(q.bots, {})
        self.assertEqual(q.materials, {})
        self.assertEqual(q.pylon, None)



class PylonTest(TestCase):


    def test_attributes(self):
        """
        A Pylon should belong to a team, have locks and the work required to
        unlock the lock.
        """
        p = Pylon(3)
        self.assertEqual(p.locks, 3)
        self.assertEqual(p.team, None)
        self.assertEqual(p.work, None)