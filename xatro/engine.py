from twisted.internet import defer

from zope.interface import implements

from xatro.interface import IEngine
from xatro.error import InvalidSolution, NotEnoughEnergy
from xatro.work import WorkMaker
from xatro.action import ConsumeEnergy



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
        try:
            self.engine.isAllowed(world, action)
        except Exception as e:
            return defer.fail(e)

        # check work
        work = self.engine.workRequirement(world, action)
        if work:
            # do they have a solution?
            solution = world.envelope(action).get('work_solution', None)
            if solution is None or not self.work_maker.isResult(work, solution):
                # verify that the work is good
                return defer.fail(InvalidSolution(work))
        
        # check energy
        energy = self.engine.energyRequirement(world, action)
        if energy:
            # do they have enough energy?
            subject_id = action.subject()
            subject = world.get(subject_id)
            available_energies = subject.get('energy', [])
            if len(available_energies) < energy:
                return defer.fail(NotEnoughEnergy(energy))

        d = defer.maybeDeferred(action.execute, world)
        
        # if the operation succeeds, consume energy
        if energy:
            d.addCallback(self._consumeEnergyAndReturn, world, action.subject(),
                          energy)
        return d


    def _consumeEnergyAndReturn(self, result, world, consumer, amount):
        """
        Consume some energy and then return the result.
        """
        ConsumeEnergy(consumer, amount).execute(world)
        return result


    def worldEventReceived(self, world, event):
        self.engine.worldEventReceived(world, event)