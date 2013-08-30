from twisted.trial.unittest import TestCase
from itertools import product
from hashlib import sha1

from xatro.work import WorkMaker


POOL = map(chr, xrange(0, 255))
MAX_SHA = int('f'*40, 16)


def validAnswer(nonce, goal, answer):
    result = int(sha1(nonce + answer).hexdigest(), 16)
    return result > goal


def _options(pool):
    """
    Return gradually lengthening selections of pool.

    For instance, if pool is ABCD, return

        A, B, C, D, AA, AB, AC, AD, BA, BB, BC, BD
    """
    i = 1
    while True:
        for p in product(pool, repeat=i):
            yield ''.join(p)
        i += 1


def findResult(nonce, goal):
    """
    Brute force a string that will satisfy the problem for the given args.
    """
    for o in _options(POOL):
        if validAnswer(nonce, goal, o):
            return o
    return ''



class WorkMakerTest(TestCase):


    def test_makeGoal(self):
        """
        Given a difficulty and a scale, you can make a goal
        """
        maker = WorkMaker()
        goal = maker.makeGoal(1, 1000)
        self.assertEqual(goal, (1000 - 1) * (maker.MAX_SHA / 1000))


    def test_makeGoal_default(self):
        """
        The default difficulty and scale should be used.
        """
        maker = WorkMaker()
        g1 = maker.makeGoal()
        g2 = maker.makeGoal(maker.difficulty, maker.scale)
        self.assertEqual(g1, g2)


    def test_getWork(self):
        """
        You can get a piece of work.
        """
        maker = WorkMaker()
        work = maker.getWork()
        self.assertEqual(work.goal, maker.makeGoal())
        self.assertNotEqual(work.nonce, None)
        self.assertNotEqual(work.nonce, '')


    def test_getWork_custom(self):
        """
        You can customize the difficulty and scale of the work requested.
        """
        maker = WorkMaker(9, 99)
        work = maker.getWork(10, 1123)
        self.assertEqual(work.goal, maker.makeGoal(10, 1123))


    def test_getWork_differentNonce(self):
        """
        The nonce should be different each time
        """
        maker = WorkMaker()
        a = maker.getWork()
        b = maker.getWork()
        self.assertNotEqual(a.nonce, b.nonce)


    def test_isResult(self):
        """
        You can verify that the result of some work is valid
        """
        maker = WorkMaker()
        work = maker.getWork()
        result = findResult(work.nonce, work.goal)
        self.assertEqual(maker.isResult(work, result), True)


    def test_isResult_False(self):
        """
        isResult should detect bad results and return False
        """
        maker = WorkMaker()
        work = maker.getWork(1, 1000000)
        self.assertEqual(maker.isResult(work, 'hey'), False)
        self.assertEqual(maker.isResult(work, None), False)


