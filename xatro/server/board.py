"""
Board and Square and such.
"""

from twisted.internet import defer
from zope.interface import implements
from xatro.server.interface import IEventReceiver, IKillable, ILocatable
from xatro.server.event import Event

from uuid import uuid4

from functools import wraps

class EnergyNotConsumedYet(Exception): pass
class NotEnoughEnergy(Exception): pass
class TooDead(Exception): pass



def preventWhenDead(f):
    """
    Decorator for preventing calls when too dead.
    """
    @wraps(f)
    def wrapped(instance, *args, **kwargs):
        if instance.dead:
            raise TooDead()
        return f(instance, *args, **kwargs)
    return wrapped



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
        self.contents = {}


    def eventReceived(self, event):
        self.board.eventReceived(event)
        for thing in self.contents.values():
            try:
                thing.eventReceived(event)
            except AttributeError:
                pass
            


    def addThing(self, thing):
        """
        Add a thing to this square.
        """
        if thing.square:
            thing.square.removeThing(thing)
        thing.square = self
        self.contents[thing.id] = thing
        self.eventReceived(Event(thing, 'entered', self))


    def removeThing(self, thing):
        """
        Remove a bot from this square.
        """
        thing.square = None
        self.contents.pop(thing.id)
        self.eventReceived(Event(thing, 'exited', self))



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



class Ore(object):
    """
    I am ore that has yet to be made into something useful.
    
    @ivar square: The square I'm in right now.
    @ivar id: My unique id.
    """

    implements(ILocatable)

    square = None

    def __init__(self):
        self.id = str(uuid4())



class Lifesource(object):
    """
    I am a lifesource for something.  If I die, the thing I'm tied to dies.

    @ivar other: The thing I'm a life source for.
    """

    implements(ILocatable, IKillable)

    square = None
    _hitpoints = 10
    dead = False


    def __init__(self, other):
        self.id = str(uuid4())
        self.other = other


    def emit(self, event):
        """
        XXX
        """
        if self.square:
            self.square.eventReceived(event)


    def hitpoints(self):
        return self._hitpoints


    @preventWhenDead
    def damage(self, amount):
        """
        XXX
        """
        self._hitpoints -= amount
        self.emit(Event(self, 'hp', -amount))


    @preventWhenDead
    def revive(self, amount):
        """
        XXX
        """
        self._hitpoints += amount
        self.emit(Event(self, 'hp', amount))


    @preventWhenDead
    def kill(self):
        """
        XXX
        """
        self._hitpoints = 0
        self.dead = True
        self.emit(Event(self, 'died', None))

        try:
            self.other.kill()
        except TooDead:
            pass



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

    implements(IEventReceiver, IKillable, ILocatable)

    team = None
    name = None
    health = 10
    dead = False
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
        Called when I receive an event (typically from the L{Square}).  This
        event is passed on to my C{event_receiver}.
        """
        self.event_receiver(event)


    def emit(self, event):
        """
        Emit an event to the square I'm on.
        """
        if self.square:
            self.square.eventReceived(event)
        else:
            self.eventReceived(event)


    @preventWhenDead
    def damage(self, amount):
        """
        Damage me by C{amount} hitpoints.

        @type amount: int
        """
        amount = min(amount, self.health)
        self.health -= amount
        self.emit(Event(self, 'hp', -amount))

        if self.health <= 0:
            self.kill()


    @preventWhenDead
    def revive(self, amount):
        """
        Restore my hitpoints by C{amount}

        @type amount: int
        """
        self.health += amount
        self.emit(Event(self, 'hp', amount))


    @preventWhenDead
    def kill(self):
        """
        Kill me dead.

        This will typically be called externally for a disconnection.
        """
        # kill
        self.health = 0
        self.dead = True
        self.emit(Event(self, 'died', None))

        # waste energy
        if self.generated_energy:
            self.generated_energy.waste()

        # remove
        self.square.removeThing(self)


    def hitpoints(self):
        return self.health


    @preventWhenDead
    def charge(self):
        """
        Use my charger to generate one L{Energy}.  There can only exist one of
        my L{Energy} at a time.  You must consume previously generated
        L{Energy} before generating more.

        @raise EnergyNotConsumedYet: If my previously charged L{Energy} has not
            yet been consumed.  
        """
        if self.generated_energy:
            raise EnergyNotConsumedYet()

        self.generated_energy = Energy()
        self.emit(Event(self, 'charged', None))

        self.receiveEnergies([self.generated_energy])
        self.generated_energy.done().addCallback(self._myEnergyConsumed)


    def canCharge(self):
        """
        Return a C{Deferred} which will fire when I'm allowed to charge again.
        """
        if not self.generated_energy:
            return defer.succeed(True)
        return self.generated_energy.done()


    def _myEnergyConsumed(self, result):
        """
        Called when an energy I produced was consumed or wasted in some way.
        """
        self.generated_energy = None


    @preventWhenDead
    def receiveEnergies(self, energies):
        """
        Receive some energies from another bot.

        @param energies: A list of L{Energy} instances.
        """
        self.energy_pool.extend(energies)
        for e in energies:
            e.done().addCallback(self._sharedEnergyGone, e)
        self.emit(Event(self, 'e.received', 1))


    def _sharedEnergyGone(self, reason, energy):
        """
        Called when energy shared with me is gone (because the other bot died,
        most likely.  Poor other bot).
        """
        # I'd rather cancel the deferred, I think
        if energy in self.energy_pool:
            self.energy_pool.remove(energy)
            self.emit(Event(self, 'e.wasted', 1))

    
    @preventWhenDead
    def consumeEnergy(self, amount):
        """
        Consume an C{amount} of energy.

        @type amount: int

        @raise NotEnoughEnergy: If I don't have that much energy.
        """
        if amount > len(self.energy_pool):
            raise NotEnoughEnergy()

        for i in xrange(amount):
            e = self.energy_pool.pop()
            e.consume()
        self.emit(Event(self, 'e.consumed', amount))


    @preventWhenDead
    def shareEnergy(self, amount, bot):
        """
        Share C{amount} energies with C{bot}.

        @type amount: int
        @type bot: L{Bot}
        
        @raise NotEnoughEnergy: If I don't have that much energy.
        """
        if amount > len(self.energy_pool):
            raise NotEnoughEnergy()

        energies = self.energy_pool[:amount]
        self.energy_pool = self.energy_pool[amount:]
        self.emit(Event(self, 'e.shared', bot))
        bot.receiveEnergies(energies)



class Energy(object):
    """
    I am energy.  ooowwaaoooohhhh
    """

    def __init__(self):
        self._dones = []
        self._result = None


    def done(self):
        """
        Returns a C{Deferred} that will fire when this energy has been consumed.
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
        Consume me, notifying everything that called L{done} previously.
        """
        self._callback('consumed')


    def waste(self):
        """
        Waste me, notifying everything that called L{done} previously.
        """
        self._callback('wasted')



