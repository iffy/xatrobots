from collections import namedtuple
from uuid import uuid4
from hashlib import sha1


Work = namedtuple('Work', ['goal', 'nonce'])



class WorkMaker(object):
    """
    I make work and verify its completeness.

    @ivar difficulty: Default difficulty if none is provided to L{makeGoal}.
    @ivar scale: Default scale if none is provided to L{makeGoal}.
    """

    MAX_SHA = int('f'*40, 16)

    def __init__(self, difficulty=10, scale=10000):
        self.difficulty = difficulty
        self.scale = scale


    def makeGoal(self, difficulty=None, scale=None):
        """
        Get a goal value from a difficulty and scale.
        """
        scale = scale or self.scale
        difficulty = difficulty or self.difficulty
        return (scale - difficulty) * (self.MAX_SHA / scale)


    def getWork(self, difficulty=None, scale=None):
        """
        Get some L{Work} to do.

        @param difficulty: Difficulty of the work.  If not provided, this will
            be the C{difficulty} set on the instance.
        @type difficulty: int

        @param scale: Scale of the work.  If not provided, this will be the
            C{scale} set on the instance.
        @type scale: int

        @return: A L{Work} instance.
        """
        nonce = sha1(str(uuid4())).hexdigest()
        return Work(self.makeGoal(difficulty, scale), nonce)


    def isResult(self, work, result):
        """
        Determine if the given C{result} is an acceptable solution for the
        C{work}.

        @return: C{True} if it's acceptable, else C{False}
        """
        return self._validAnswer(work.nonce, work.goal, result)


    def _validAnswer(self, nonce, goal, answer):
        """
        Verify that the given C{answer} produces a hash greater than the
        threshold defined by C{difficulty} and C{scale}.
        """
        result = int(sha1(nonce + answer).hexdigest(), 16)
        return result > goal