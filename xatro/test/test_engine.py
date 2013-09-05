from twisted.trial.unittest import TestCase
from zope.interface.verify import verifyObject

from mock import MagicMock

from xatro.world import World
from xatro.work import Work
from xatro.error import InvalidSolution
from xatro.interface import IEngine
from xatro.engine import XatroEngine

# workRequirement(action)
# energyRequirement(action)
# isAllowed(action)


class XatroEngineTest(TestCase):


    def test_IEngine(self):
        verifyObject(IEngine, XatroEngine(None))


    def test_wraps(self):
        """
        Should wrap another engine
        """
        wrapped = MagicMock()
        e = XatroEngine(wrapped)
        self.assertEqual(e.engine, wrapped)


    def friendlyEngine(self):
        """
        Return a XatroEngine whose internal engine will let any action happen.
        """
        wrapped = MagicMock()
        wrapped.workRequirement.return_value = None
        wrapped.energyRequirement.return_value = 0
        wrapped.isAllowed.return_value = None

        e = XatroEngine(wrapped)
        return e


    def test_execute(self):
        """
        If there's no work or energy requirement and the command is allowed,
        then execute it.
        """
        e = self.friendlyEngine()

        world = MagicMock()
        action = MagicMock()
        action.execute.return_value = 'foo'

        r = e.execute(world, action)

        e.engine.isAllowed.assert_called_once_with(world, action)
        e.engine.workRequirement.assert_called_once_with(world, action)
        e.engine.energyRequirement.assert_called_once_with(world, action)

        action.execute.assert_called_once_with(world)
        self.assertEqual(r, 'foo', "Should return the value of the "
                         "execution")


    def test_execute_workRequired_fail(self):
        """
        If work is required, fail if there's not a satisfactory solution
        provided on the action's envelope.
        """
        e = self.friendlyEngine()
        
        # require some work
        e.engine.workRequirement.return_value = Work(int('f'*40, 16), 'nonce')
        
        # fail to do an action since no work is provided.
        world = World(MagicMock())
        action = MagicMock()
        self.assertRaises(InvalidSolution, e.execute, world, action)

        # fail to do the action since the work provided is wrong.
        world.envelope(action)['work_solution'] = 'hey'
        self.assertRaises(InvalidSolution, e.execute, world, action)


    def test_execute_workRequired_succeed(self):
        """
        If work is required, succeed if the solution is good.
        """
        e = self.friendlyEngine()
        e.engine.workRequirement.return_value = Work(0, 'bar')

        world = World(MagicMock())
        action = MagicMock()
        world.envelope(action)['work_solution'] = 'anything will work'

        e.execute(world, action)
        action.execute.assert_called_once_with(world)


