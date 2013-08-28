from twisted.trial.unittest import TestCase
from itertools import product
from hashlib import sha1

from xatro.work import WorkMaker, Work


POOL = map(chr, xrange(0, 255))
MAX_SHA = int('f'*40, 16)


def validAnswer(nonce, difficulty, scale, answer):
    result = int(sha1(nonce + answer).hexdigest(), 16)
    threshold = (scale - difficulty) * (MAX_SHA / scale)
    return result > threshold


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


def findResult(nonce, difficulty, scale):
    """
    Brute force a string that will satisfy the problem for the given args.
    """
    for o in _options(POOL):
        if validAnswer(nonce, difficulty, scale, o):
            return o
    return ''



class WorkMakerTest(TestCase):


    def test_getWork(self):
        """
        You can get a piece of work.
        """
        maker = WorkMaker()
        work = maker.getWork()
        self.assertEqual(work.difficulty, maker.difficulty)
        self.assertEqual(work.scale, maker.scale)
        self.assertNotEqual(work.nonce, None)
        self.assertNotEqual(work.nonce, '')


    def test_getWork_custom(self):
        """
        You can customize the difficulty and scale of the work requested.
        """
        maker = WorkMaker()
        work = maker.getWork(9, 99)
        self.assertEqual(work.difficulty, 9)
        self.assertEqual(work.scale, 99)


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
        result = findResult(work.nonce, work.difficulty, work.scale)
        self.assertEqual(maker.isResult(work, result), True)


    def test_isResult_False(self):
        """
        isResult should detect bad results and return False
        """
        maker = WorkMaker()
        work = Work(1, 100000, 'foo')
        self.assertEqual(maker.isResult(work, 'hey'), False)        
