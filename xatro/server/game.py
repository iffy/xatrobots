from twisted.python import log
from zope.interface import implements
from xatro.server.interface import IGameRules, IEventReceiver
from xatro.work import WorkMaker, InvalidSolution
from xatro.server.board import Pylon



class Game(object):
    """
    I am the place all the game pieces (squares, board, bots) go to get
    game-related specifics and to perform actions.
    """

    implements(IEventReceiver)


    def __init__(self):
        self._event_receivers = []


    def subscribe(self, func):
        """
        Subscribe to events this Game receives
        """
        self._event_receivers.append(func)


    def unsubscribe(self, func):
        """
        Unsubscribe from events this Game receives.
        """
        self._event_receivers.remove(func)


    def eventReceived(self, event):
        """
        An event was received.
        """
        for f in self._event_receivers:
            try:
                f(event)
            except Exception as e:
                log.err('Error calling event receiver:')
                log.err(str(e))




class StaticRules(object):
    """
    I am a set of game rules that doesn't change over the course of the game.
    My responses are determined by initialized settings.

    @ivar default_energy_requirement: Amount of energy required to perform
        actions by default.

    @ivar bot_hitpoints: The number of hitpoints bots start with.

    @ivar locks_after_capture: The number of locks to be put on a Pylon after
        it is captured.
    @ivar starting_locks: The number of locks a pylon has when created.
    """

    implements(IGameRules)

    default_energy_requirement = 0
    bot_hitpoints = 10

    # pylons
    locks_after_capture = 3
    starting_locks = 3


    def __init__(self):
        self._solution_checker = WorkMaker()
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


    def assertSolution(self, proposed_solution, work):
        """
        XXX
        """
        if not self._solution_checker.isResult(work, proposed_solution):
            raise InvalidSolution(work)


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


    def handle_e_gone(self, (bot, verb, ignore)):
        """
        When a bot's energy is consumed in whatever way, set the charging_work
        for the next energy to be produced.
        """
        bot.charging_work = self.charge_work_maker.getWork()


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
            return bot.charging_work
        elif action == 'addLock':
            return args[0].tolock
        elif action == 'breakLock':
            return args[0].tobreak


    def isAllowed(self, bot, action, *args, **kwargs):
        """
        XXX
        """

