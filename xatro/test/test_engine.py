from twisted.trial.unittest import TestCase
from twisted.internet import defer
from zope.interface.verify import verifyObject

from mock import MagicMock

from xatro.world import World
from xatro.work import Work
from xatro.error import InvalidSolution, NotAllowed, NotEnoughEnergy
from xatro.interface import IEngine
from xatro.engine import XatroEngine
from xatro.action import Charge

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


    @defer.inlineCallbacks
    def test_execute(self):
        """
        If there's no work or energy requirement and the command is allowed,
        then execute it.
        """
        e = self.friendlyEngine()

        world = MagicMock()
        action = MagicMock()
        action.execute.return_value = 'foo'

        r = yield e.execute(world, action)

        e.engine.isAllowed.assert_called_once_with(world, action)
        e.engine.workRequirement.assert_called_once_with(world, action)
        e.engine.energyRequirement.assert_called_once_with(world, action)

        action.execute.assert_called_once_with(world)
        self.assertEqual(r, 'foo', "Should return the value of the "
                         "execution")


    @defer.inlineCallbacks
    def test_execute_Deferred(self):
        """
        If the command returns a Deferred, that should be handled okay.
        """
        e = self.friendlyEngine()

        world = MagicMock()
        action = MagicMock()
        action.execute.return_value = defer.succeed('foo')

        r = yield e.execute(world, action)

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
        self.assertFailure(e.execute(world, action), InvalidSolution)

        # fail to do the action since the work provided is wrong.
        world.envelope(action)['work_solution'] = 'hey'
        self.assertFailure(e.execute(world, action), InvalidSolution)


    @defer.inlineCallbacks
    def test_execute_workRequired_succeed(self):
        """
        If work is required, succeed if the solution is good.
        """
        e = self.friendlyEngine()
        e.engine.workRequirement.return_value = Work(0, 'bar')

        world = World(MagicMock())
        action = MagicMock()
        world.envelope(action)['work_solution'] = 'anything will work'

        yield e.execute(world, action)
        action.execute.assert_called_once_with(world)


    def test_execute_notAllowed(self):
        """
        If an action is not allowed, don't do it.
        """
        e = self.friendlyEngine()
        
        # require some work
        e.engine.isAllowed.side_effect = NotAllowed('foo')
        
        # fail to do an action since no work is provided.
        world = World(MagicMock())
        action = MagicMock()
        self.assertFailure(e.execute(world, action), NotAllowed)


    def test_execute_energyRequired_fail(self):
        """
        If energy is required, fail to do the action if there's not enough
        energy.
        """
        e = self.friendlyEngine()

        # require some energy
        e.engine.energyRequirement.return_value = 2

        # fail to do an action since energy is required
        world = World(MagicMock())
        actor = world.create('foo')
        action = MagicMock()
        action.subject.return_value = actor['id'] 
        self.assertFailure(e.execute(world, action), NotEnoughEnergy)


    @defer.inlineCallbacks
    def test_execute_energyRequired_succeed(self):
        """
        If energy is required and the actor has enough energy, do the action.
        """
        e = self.friendlyEngine()

        # require some energy
        e.engine.energyRequirement.return_value = 2

        # make some energy
        world = World(MagicMock())

        actor = world.create('thing')
        yield Charge(actor['id']).execute(world)
        yield Charge(actor['id']).execute(world)
        self.assertEqual(len(actor['energy']), 2)

        # do the action and consume the energy
        action = MagicMock()
        action.subject.return_value = actor['id']
        action.execute.return_value = 'foo'
        
        ret = yield e.execute(world, action)
        self.assertEqual(ret, 'foo', "Should have executed the action")
        self.assertEqual(len(actor['energy']), 0, "Should have consumed "
                         "the energy")


    @defer.inlineCallbacks
    def test_execute_energyRequired_command_fails(self):
        """
        If there is energy required and the command fails to run, the energy
        should not be consumed.
        """
        e = self.friendlyEngine()

        # require some energy
        e.engine.energyRequirement.return_value = 2

        # make some energy
        world = World(MagicMock())

        actor = world.create('thing')
        yield Charge(actor['id']).execute(world)
        yield Charge(actor['id']).execute(world)
        self.assertEqual(len(actor['energy']), 2)

        # do the action and consume the energy
        action = MagicMock()
        action.subject.return_value = actor['id']

        # synchronous
        action.execute.side_effect = NotAllowed('foo')
        self.assertFailure(e.execute(world, action), NotAllowed)
        self.assertEqual(len(actor['energy']), 2, "Should not have consumed "
                         "the energy")

        # asynchronous
        action.execute.side_effect = None
        action.execute.return_value = defer.fail(NotAllowed('foo'))
        self.assertFailure(e.execute(world, action), NotAllowed)
        self.assertEqual(len(actor['energy']), 2, "Should not have consumed "
                         "the energy")



