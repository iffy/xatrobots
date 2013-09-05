from zope.interface import implements

from xatro.interface import IEngine
from xatro.error import InvalidSolution
from xatro.work import WorkMaker



class XatroEngine(object):
    """
    I am a world engine that lets you play the xatrobots game.  I introduce
    the concepts of work and energy requirements into the world.  Specifics
    are taken care of by an L{IXatroEngine} instance which I wrap.
    """

    implements(IEngine)


    def __init__(self, engine):
        self.engine = engine
        self.work_maker = WorkMaker()


    def execute(self, world, action):
        """
        """
        self.engine.isAllowed(world, action)

        work = self.engine.workRequirement(world, action)
        if work:
            # do they have a solution?
            solution = world.envelope(action).get('work_solution', None)
            if solution is None or not self.work_maker.isResult(work, solution):
                # verify that the work is good
                raise InvalidSolution(work)
        self.engine.energyRequirement(world, action)

        return action.execute(world)