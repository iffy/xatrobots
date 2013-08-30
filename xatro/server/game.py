from zope.interface import implements
from xatro.server.interface import IGameRules
from xatro.work import WorkMaker
from xatro.server.board import Pylon



class GameShell(object):
    """
    I am a the place all the game pieces (squares, board, bots) go to get
    game-related specifics and to perform actions.
    """

    rules = None
    board = None
    event_receiver = None


    def __init__(self, rules=None):
        self.rules = rules



class StaticRules(object):
    """
    I am a set of game rules that doesn't change over the course of the game.
    My responses are determined by initialized settings.

    @ivar default_energy_requirement: Amount of energy required to perform
        actions by default.

    @ivar bot_hitpoints: The number of hitpoints bots start with.

    @ivar locks_after_capture: The number of locks to be put on a Pylon after
        it is captured.
    """

    implements(IGameRules)

    default_energy_requirement = 0
    bot_hitpoints = 10

    # pylons
    locks_after_capture = 3
    starting_locks = 3


    def __init__(self):
        self.charge_work_maker = WorkMaker()
        self.addLock_work_maker = WorkMaker()
        self.breakLock_work_maker = WorkMaker()
        self.energy_requirements = {
            'makeTool': 1,
            'openPortal': 1,
            'breakLock': 3,
            'addLock': 3,
            'move': 2,
        }
        self.energy_to_hp = {
            'heal': {},
            'shoot': {}
        }
        self.default_energy_to_hp = {
            1: 1,
            2: 3,
            3: 6,
        }


    def energyRequirement(self, bot, action, *args, **kwargs):
        """
        XXX
        """
        return self.energy_requirements.get(action,
                                            self.default_energy_requirement)


    def eventReceived(self, event):
        """
        XXX
        """
        handler = getattr(self, 'handle_' + event.verb, lambda x:None)
        return handler(event)


    def handle_joined(self, (bot, verb, ign)):
        """
        When a bot joins the game, give it hitpoints.
        """
        bot.setHitpoints(self.bot_hitpoints)


    def handle_lock_broken(self, (bot, verb, pylon)):
        """
        When a lock is broken, update all the work efforts for locks.
        """
        self._updatePylonWork(pylon)


    def handle_lock_added(self, (bot, verb, pylon)):
        """
        When a lock is added, update all the work efforts for locks.
        """
        self._updatePylonWork(pylon)


    def handle_pylon_locks(self, (pylon, verb, locks)):
        """
        When the number of locks on a pylon is changed, update the work
        required to lock/break locks.
        """
        self._updatePylonWork(pylon)


    def _updatePylonWork(self, pylon):
        pylon.setLockWork(self.addLock_work_maker.getWork())
        pylon.setBreakLockWork(self.breakLock_work_maker.getWork())


    def handle_pylon_captured(self, (bot, verb, pylon)):
        """
        When a pylon is captured, apply a set of locks for the new team.
        """
        pylon.setLocks(self.locks_after_capture)


    def handle_entered(self, (subject, verb, square)):
        if isinstance(subject, Pylon):
            subject.setLocks(self.starting_locks)


    def energyToHitpoints(self, bot, action, target, energy):
        """
        XXX
        """
        default = self.default_energy_to_hp
        d = self.energy_to_hp.get(action, default)
        if energy in d:
            return d[energy]
        return default[energy]


    def workRequirement(self, bot, action, *args, **kwargs):
        """
        XXX
        """
        if action == 'charge':
            return self.charge_work_maker.getWork()
        elif action == 'addLock':
            return self.addLock_work_maker.getWork()
        elif action == 'breakLock':
            return self.breakLock_work_maker.getWork()

