from collections import namedtuple
from uuid import uuid4
from hashlib import sha1


Work = namedtuple('Work', ['difficulty', 'scale', 'nonce'])



class WorkMaker(object):
    """
    I make work and verify its completeness.

    @ivar difficulty: Default difficulty if none is provided to L{getWork}.
    @ivar scale: Default scale if none is provided to L{getWork}.
    """

    difficulty = 10
    scale = 10000

    MAX_SHA = int('f'*40, 16)


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
        return Work(difficulty or self.difficulty, scale or self.scale, nonce)


    def isResult(self, work, result):
        """
        Determine if the given C{result} is an acceptable solution for the
        C{work}.

        @return: C{True} if it's acceptable, else C{False}
        """
        return self._validAnswer(work.nonce, work.difficulty, work.scale,
                                 result)


    def _validAnswer(self, nonce, difficulty, scale, answer):
        """
        Verify that the given C{answer} produces a hash greater than the
        threshold defined by C{difficulty} and C{scale}.
        """
        result = int(sha1(nonce + answer).hexdigest(), 16)
        threshold = (scale - difficulty) * (self.MAX_SHA / scale)
        return result > threshold


    def workFor(self, action, obj):
        """
        Get some L{Work} for a specific type of action.

        @param action: Name of the action.  I ignore this.
        @param obj: Object involved with the action.  I ignore this, too.

        @return: A L{Work} instance.
        """
        return self.getWork()