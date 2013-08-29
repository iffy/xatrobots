"""
Board and Square and such.
"""

from twisted.internet import defer
from zope.interface import implements
from xatro.server.interface import IEventReceiver, IKillable
from xatro.server.event import Event

from uuid import uuid4

class EnergyNotConsumedYet(Exception): pass
class NotEnoughEnergy(Exception): pass


class Square(object):
    """
    I am a square on the gameboard.

    @ivar board: L{Board} instance.
    @ivar pylon: L{Pylon} instance.
    @ivar bots: Dictionary of bots in this square.
    @ivar materials: Dictionary of materials in this square.
    """

    implements(IEventReceiver)

    board = None
    events = None
    pylon = None


    def __init__(self, board):
        self.id = str(uuid4())
        self.board = board
        self.bots = {}
        self.materials = {}


    def eventReceived(self, event):
        self.board.eventReceived(event)
        for bot in self.bots.values():
            bot.eventReceived(event)


    def addBot(self, bot):
        """
        Add a bot to this square.
        """
        if bot.square:
            bot.square.removeBot(bot)
        bot.square = self
        self.bots[bot.id] = bot
        self.eventReceived(Event(bot, 'entered', self))


    def removeBot(self, bot):
        """
        Remove a bot from this square.
        """
        bot.square = None
        del self.bots[bot.id]
        self.eventReceived(Event(bot, 'exited', self))



class Pylon(object):
    """
    I am a pylon within a square.

    @ivar square: The square I'm in right now.

    @ivar team: Team name that owns me
    @type team: str

    @ivar unlock_work: The L{Work} required to unlock the next lock.
    @ivar lock_work: The L{Work} required to add another lock.
    """

    square = None
    team = None
    unlock_work = None
    lock_work = None

    def __init__(self, locks):
        self.locks = locks



class Material(object):
    """
    I am a material.

    @ivar health: If an integer, the current health of the material.
    @ivar current_use: C{None} if not in use, otherwise this is the object
        I've been provisioned into.
    @ivar square: The square I'm in right now.
    """

    square = None
    health = None
    current_use = None


    def __init__(self):
        self.id = str(uuid4())



class Bot(object):
    """
    I am a bot in play.

    @ivar team: Team name
    @ivar name: Bot name
    @ivar health: Amount of health left. 0 = dead.
    @ivar equipment: Any piece of equipment I have.
    @ivar portal: The portal where I landed.
    @ivar square: The square I'm in right now.

    @ivar energy: List of the L{Energy} available to me.  This may
        include L{Energy} shared with me by other L{Bot}s.
    @ivar generated_energy: The L{Energy} I last generated (if it hasn't been
        consumed yet).  This may have been shared with another L{Bot} and so
        won't be found in my C{energy_pool}.
    """

    implements(IEventReceiver, IKillable)

    team = None
    name = None
    health = 10
    equipment = None
    portal = None
    square = None


    def __init__(self, team, name, event_receiver=None):
        self.id = str(uuid4())
        self.team = team
        self.name = name
        self.energy_pool = []
        self.generated_energy = None
        self.event_receiver = event_receiver or (lambda x:None)


    def eventReceived(self, event):
        """
        XXX
        """
        self.event_receiver(event)


    def emit(self, event):
        """
        XXX
        """
        if self.square:
            self.square.eventReceived(event)
        else:
            self.eventReceived(event)


    def damage(self, amount):
        """
        XXX
        """
        self.health -= amount
        self.emit(Event(self, 'health', -amount))


    def revive(self, amount):
        """
        XXX
        """
        self.health += amount
        self.emit(Event(self, 'health', amount))


    def kill(self):
        """
        XXX
        """
        # kill
        self.health -= self.health
        self.emit(Event(self, 'died', None))

        # waste energy
        if self.generated_energy:
            self.generated_energy.waste()

        # remove
        self.square.removeBot(self)


    def hitpoints(self):
        return self.health


    def charge(self):
        """
        XXX
        """
        if self.generated_energy:
            raise EnergyNotConsumedYet()

        self.generated_energy = Energy()
        self.emit(Event(self, 'charged', None))

        self.receiveEnergy([self.generated_energy])
        self.generated_energy.done().addCallback(self._myEnergyConsumed)


    def canCharge(self):
        """
        XXX
        """
        if not self.generated_energy:
            return defer.succeed(True)
        return self.generated_energy.done()


    def _myEnergyConsumed(self, result):
        """
        XXX
        """
        self.generated_energy = None


    def receiveEnergy(self, energies):
        """
        XXX

        @param energies: A list of L{Energy} instances.
        """
        self.energy_pool.extend(energies)
        for e in energies:
            e.done().addCallback(self._sharedEnergyGone, e)
        self.emit(Event(self, 'e.received', 1))


    def _sharedEnergyGone(self, reason, energy):
        """
        XXX
        """
        # I'd rather cancel the deferred, I think
        if energy in self.energy_pool:
            self.energy_pool.remove(energy)
            self.emit(Event(self, 'e.wasted', 1))


    def consumeEnergy(self, amount):
        """
        XXX
        """
        if amount > len(self.energy_pool):
            raise NotEnoughEnergy()

        for i in xrange(amount):
            e = self.energy_pool.pop()
            e.consume()
        self.emit(Event(self, 'e.consumed', amount))


    def shareEnergy(self, amount, bot):
        """
        XXX
        """
        if amount > len(self.energy_pool):
            raise NotEnoughEnergy()

        energies = self.energy_pool[:amount]
        self.energy_pool = self.energy_pool[amount:]
        self.emit(Event(self, 'e.shared', bot))
        bot.receiveEnergy(energies)



class Energy(object):
    """
    I am energy.  ooowwaaoooohhhh
    """

    def __init__(self):
        self._dones = []
        self._result = None


    def done(self):
        """
        XXX
        """
        if self._result:
            return defer.succeed(self._result)
        d = defer.Deferred()
        self._dones.append(d)
        return d


    def _callback(self, result):
        self._result = result
        for d in self._dones:
            d.callback(result)


    def consume(self):
        """
        XXX
        """
        self._callback('consumed')


    def waste(self):
        """
        XXX
        """
        self._callback('wasted')



