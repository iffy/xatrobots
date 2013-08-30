"""
Board and Square and such.
"""

from twisted.internet import defer
from zope.interface import implements
from xatro.server.interface import IEventReceiver, IKillable, ILocatable
from xatro.server.event import Event

from hashlib import sha1

from uuid import uuid4

from functools import wraps
from collections import namedtuple

class EnergyNotConsumedYet(Exception): pass
class NotEnoughEnergy(Exception): pass
class NotOnSquare(Exception): pass
class LackingTool(Exception): pass
class NotAllowed(Exception): pass



Coord = namedtuple('Coord', ['x', 'y'])


def requireSquare(f):
    """
    Decorator for preventing calls when too dead.
    """
    @wraps(f)
    def wrapped(instance, *args, **kwargs):
        if not instance.square:
            raise NotOnSquare()
        return f(instance, *args, **kwargs)
    return wrapped



class DeferredBroadcaster(object):
    """
    XXX
    """

    has_result = False
    result = None

    def __init__(self):
        self.pending = []


    def get(self):
        if self.has_result:
            return defer.succeed(self.result)
        d = defer.Deferred()
        self.pending.append(d)
        return d


    def callback(self, result):
        self.has_result = True
        self.result = result
        for d in self.pending:
            d.callback(result)



class Board(object):
    """
    I am a game board.  I keep track of all the squares and pass square events
    up to the game.
    """

    implements(IEventReceiver)

    game = None


    def __init__(self, game=None):
        self.game = game
        self.squares = {}
        self.bots = {}


    def eventReceived(self, event):
        """
        Called when I receive an event.
        """
        if self.game:
            self.game.eventReceived(event)


    def addSquare(self, coord):
        """
        Add a square to me for the given coordinates.

        @param coord: A tuple (x,y).

        @raise NotAllowed: If the coordinate is already occupied by a square.
        """
        if coord in self.squares:
            raise NotAllowed('%r is already occupied' % (coord,))

        square = Square(self)
        self.squares[coord] = square
        square.coordinates = coord

        self.eventReceived(Event(self, 'square_added', square))
        return square


    def adjacentSquares(self, square):
        """
        Return the list of squares that are adjacent to the given square.
        """
        x,y = square.coordinates
        poss = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
        return [self.squares[c] for c in poss if c in self.squares]


    def addBot(self, bot):
        """
        Called to indicate that the bot has joined the game.
        """
        self.bots[bot.id] = bot
        self.eventReceived(Event(bot, 'joined', self))


    def removeBot(self, bot):
        """
        Called to indicate that the bot has quit the game.
        """
        self.bots.pop(bot.id)
        self.eventReceived(Event(bot, 'quit', self))



class Square(object):
    """
    I am a square on the gameboard.

    @ivar id: My id
    @ivar board: L{Board} instance.
    @ivar pylon: L{Pylon} instance.
    @ivar bots: Dictionary of bots in this square.
    @ivar materials: Dictionary of materials in this square.
    """

    implements(IEventReceiver)

    board = None
    events = None
    pylon = None
    coordinates = None


    def __init__(self, board):
        self.id = str(uuid4())
        self.board = board
        self._contents = {}


    def eventReceived(self, event):
        self.board.eventReceived(event)
        for thing in self._contents.values():
            try:
                thing.eventReceived(event)
            except AttributeError:
                pass


    def onGame(self, func, *args, **kwargs):
        """
        Call the named function on the game.
        """
        return self.board.onGame(func, *args, **kwargs)


    def addThing(self, thing):
        """
        Add a thing to this square.
        """
        if thing.square:
            thing.square.removeThing(thing)
        thing.square = self
        self._contents[thing.id] = thing
        self.eventReceived(Event(thing, 'entered', self))


    def removeThing(self, thing):
        """
        Remove a bot from this square.
        """
        thing.square = None
        self._contents.pop(thing.id)
        self.eventReceived(Event(thing, 'exited', self))


    def contents(self, cls=None):
        """
        Return a list of all the things on this square.
        """
        if cls:
            return [x for x in self._contents.values() if isinstance(x, cls)]
        return list(self._contents.values())



class Pylon(object):
    """
    I am a pylon within a square.

    @ivar square: The square I'm in right now.

    @ivar team: Team name that owns me
    @type team: str

    @ivar tobreak: The L{Work} required to break the next lock.
    @ivar tolock: The L{Work} required to add another lock.
    """

    implements(ILocatable)

    square = None
    locks = 3
    team = None
    tobreak = None
    tolock = None

    def __init__(self):
        self.id = str(uuid4())


    def emit(self, event):
        """
        Emit an event to my containing Square.
        """
        if self.square:
            self.square.eventReceived(event)


    def setLocks(self, number):
        """
        Set the number of locks on me.
        """
        self.locks = number
        self.emit(Event(self, 'pylon_locks', number))


    def setLockWork(self, work):
        """
        Set the work required to add another lock to this Pylon.
        """
        self.tolock = work
        self.emit(Event(self, 'pylon_tolock', work))


    def setBreakLockWork(self, work):
        """
        Set the work required to break the next lock.
        """
        self.tobreak = work
        self.emit(Event(self, 'pylon_tobreak', work))



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



class Tool(object):
    """
    I am a tool that a bot can use.  I come from ore and have a lifesource.

    @ivar kind: The kind of tool I am.  Bots care about this.
    @type kind: str

    @ivar lifesource: The lifesource I came from, maybe.  It could be None.
    """

    dead = False


    def __init__(self, kind, lifesource=None):
        self.kind = kind
        self.lifesource = lifesource
        self._destruction_broadcaster = DeferredBroadcaster()


    def destroyed(self):
        """
        Return a deferred which will fire when I'm destroyed.
        """
        return self._destruction_broadcaster.get()


    def kill(self):
        """
        Kill me, notifying things that care.
        """
        self._destruction_broadcaster.callback(self)



class Lifesource(object):
    """
    I am a lifesource for something.  If I die, the thing I'm tied to dies.

    @ivar other: The thing I'm a life source for.
    @ivar square: Square I'm on.
    @ivar dead: C{True} means I'm dead.
    """

    implements(ILocatable, IKillable)

    other = None
    _other_d = None
    square = None
    _hitpoints = 10
    dead = False


    def __init__(self, other=None):
        self.id = str(uuid4())
        self._destruction_broadcaster = DeferredBroadcaster()
        if other:
            self.pairWith(other)


    @requireSquare
    def pairWith(self, other):
        """
        Forever entwine myself with the `other` (or until I am paired with
        another).  Once paired, if the other is destroyed, I will die.  If I
        die, I will take the other down with me.
        """
        if self.other:
            # cancel previous pairing
            self._other_d.cancel()
        self.other = other

        # watch for the death of the other
        self._other_d = d = other.destroyed()
        d.addCallback(lambda x:self.kill())
        d.addErrback(lambda err: err.trap(defer.CancelledError))


    def emit(self, event):
        """
        Emit an event to my square.
        """
        if self.square:
            self.square.eventReceived(event)


    def hitpoints(self):
        return self._hitpoints


    @requireSquare
    def damage(self, amount):
        """
        Cause me damage.
        """
        amount = min(self._hitpoints, amount)
        self._hitpoints -= amount
        self.emit(Event(self, 'hp', -amount))

        if self._hitpoints == 0:
            self.kill()


    @requireSquare
    def revive(self, amount):
        """
        Give me life.
        """
        self._hitpoints += amount
        self.emit(Event(self, 'hp', amount))


    @requireSquare
    def kill(self):
        """
        Kill me.
        """
        self._hitpoints = 0
        self.dead = True
        self.emit(Event(self, 'died', None))

        # kill the thing I support
        if self.other:
            try:
                self.other.kill()
            except NotOnSquare:
                pass

        # replace myself with Ore
        square = self.square
        square.removeThing(self)
        square.addThing(Ore())

        # notify others
        self._destruction_broadcaster.callback(self)


    def destroyed(self):
        """
        Return a deferred which will fire when I'm destroyed.
        """
        return self._destruction_broadcaster.get()



def requireTool(required_tool):
    """
    Decorator for requiring the bot to have the specified tool in order to
    execute this function.

    @param required_tool: String name of the tool required in order to run
        the function this decorates.
    """
    def deco(f):
        @wraps(f)
        def wrapped(instance, *args, **kwargs):
            if not instance.tool or instance.tool.kind != required_tool:
                raise LackingTool(required_tool)
            return f(instance, *args, **kwargs)
        return wrapped
    return deco



class Bot(object):
    """
    I am a bot in play.

    @ivar team: Team name
    @ivar name: Bot name
    @ivar tool: A tool I have.
    @ivar portal: The portal where I landed.
    @ivar square: The square I'm in right now.

    @ivar energy_pool: List of the L{Energy} available to me.  This may
        include L{Energy} shared with me by other L{Bot}s.
    
    @ivar generated_energy: The L{Energy} I last generated (if it hasn't been
        consumed yet).  This may have been shared with another L{Bot} and so
        won't be found in my C{energy_pool}.

    @ivar charging_work: The L{Work} required to charge.  This will be C{None}
        if I'm currently not allowed to charge.
    
    @ivar event_receiver: A function that will be called with every L{Event}
        I see.
    """

    implements(IEventReceiver, IKillable, ILocatable)

    team = None
    name = None
    _hitpoints = None
    dead = False
    tool = None
    portal = None
    square = None


    def __init__(self, team, name, event_receiver=None):
        self.id = str(uuid4())
        self.team = team
        self.name = name
        self.energy_pool = []
        self.generated_energy = None
        self.charging_work = None
        self.event_receiver = event_receiver or (lambda x:None)
        self._destruction_broadcaster = DeferredBroadcaster()


    def _requireSameSquare(self, other):
        """
        @raise NotAllowed: If the other thing isn't on the same square as me.
        """
        if self.square is None or self.square != other.square:
            raise NotAllowed("Not on the same square")


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


    @requireSquare
    def damage(self, amount):
        """
        Damage me by C{amount} hitpoints.

        @type amount: int
        """
        amount = min(amount, self._hitpoints)
        self._hitpoints -= amount
        self.emit(Event(self, 'hp', -amount))

        if self._hitpoints <= 0:
            self.kill()


    @requireSquare
    def revive(self, amount):
        """
        Restore my hitpoints by C{amount}

        @type amount: int
        """
        self._hitpoints += amount
        self.emit(Event(self, 'hp', amount))


    @requireSquare
    def kill(self):
        """
        Kill me dead.

        This will typically be called externally for a disconnection.
        """
        # kill
        self._hitpoints = 0
        self.dead = True
        self.emit(Event(self, 'died', None))

        # waste energy
        if self.generated_energy:
            self.generated_energy.waste()

        # destroy tool
        if self.tool:
            self.tool.kill()

        # remove
        self.square.removeThing(self)

        # notify others
        self._destruction_broadcaster.callback(self)


    def destroyed(self):
        """
        Return a Deferred which fires when I've been destroyed.
        """
        return self._destruction_broadcaster.get()


    def hitpoints(self):
        return self._hitpoints


    def setHitpoints(self, hp):
        """
        Set the number of hitpoints that this bot has.
        """
        self._hitpoints = hp
        self.emit(Event(self, 'hp_set', hp))


    @requireSquare
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
        self.charging_work = None
        self.emit(Event(self, 'charged', None))

        self.receiveEnergies([self.generated_energy])
        self.generated_energy.done().addCallback(self._myEnergyConsumed)


    @requireSquare
    def canCharge(self):
        """
        Return a C{Deferred} which will fire when I'm allowed to charge again.

        @return: A C{Deferred} which will fire with a L{Work} instance.
        """
        if self.charging_work:
            # asked before and you can charge now
            return defer.succeed(self.charging_work)
        elif self.generated_energy:
            # waiting on energy to be consumed
            d = self.generated_energy.done()
            return d.addCallback(lambda x:self._getChargingWork())
        else:
            # first time asking
            return defer.succeed(self._getChargingWork())
    

    def _getChargingWork(self):
        """
        XXX
        """
        if self.charging_work:
            return self.charging_work
        self.charging_work = self.square.workFor(self, 'charge', None)
        return self.charging_work


    def _myEnergyConsumed(self, result):
        """
        Called when an energy I produced was consumed or wasted in some way.
        """
        self.generated_energy = None


    @requireSquare
    def receiveEnergies(self, energies):
        """
        Receive some energies from another bot.

        @param energies: A list of L{Energy} instances.
        """
        self.energy_pool.extend(energies)
        for e in energies:
            e.done().addCallback(self._sharedEnergyGone, e)
        self.emit(Event(self, 'e_received', 1))


    def _sharedEnergyGone(self, reason, energy):
        """
        Called when energy shared with me is gone (because the other bot died,
        most likely.  Poor other bot).
        """
        # I'd rather cancel the deferred, I think
        if energy in self.energy_pool:
            self.energy_pool.remove(energy)
            self.emit(Event(self, 'e_wasted', 1))

    
    @requireSquare
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
        self.emit(Event(self, 'e_consumed', amount))


    @requireSquare
    def shareEnergy(self, amount, bot):
        """
        Share C{amount} energies with C{bot}.

        @type amount: int
        @type bot: L{Bot}
        
        @raise NotEnoughEnergy: If I don't have that much energy.
        @raise NotAllowed: If the other bot isn't in the same square.
        """
        self._requireSameSquare(bot)

        if amount > len(self.energy_pool):
            raise NotEnoughEnergy()

        energies = self.energy_pool[:amount]
        self.energy_pool = self.energy_pool[amount:]
        self.emit(Event(self, 'e_shared', bot))
        bot.receiveEnergies(energies)


    @requireSquare
    def equip(self, tool):
        """
        Equip this bot with a tool.
        """
        self.tool = tool
        self.emit(Event(self, 'equipped', tool))

        tool.destroyed().addCallback(self._toolDestroyed)


    def _toolDestroyed(self, tool):
        """
        Called when a tool is destroyed.
        """
        self.tool = None
        self.emit(Event(self, 'unequipped', None))


    @requireSquare
    @requireTool('cannon')
    def shoot(self, what, damage):
        """
        Shoot something.

        @param what: An L{IKillable}
        @param damage: Amount of damage to do.
        @type damage: int
        """
        self._requireSameSquare(what)

        self.emit(Event(self, 'shot', what))
        what.damage(damage)


    @requireSquare
    @requireTool('repair kit')
    def heal(self, what, amount):
        """
        Heal something.

        @param what: An L{IKillable}
        @param amount: Amount of hitpoints to give.
        @type amount: int
        """
        self._requireSameSquare(what)

        self.emit(Event(self, 'healed', what))
        what.revive(amount)


    @requireSquare
    @requireTool('portal')
    def openPortal(self, code):
        """
        Open a portal to be used with a code.
        """
        self.tool.pw_hash = sha1(code).hexdigest()
        self.emit(Event(self, 'portal_open', None))


    def usePortal(self, bot, code):
        """
        Use a bot's portal with the given code and land on the board.
        """
        if self.square:
            raise NotAllowed('You have already landed on the board')
        
        if sha1(code).hexdigest() != bot.tool.pw_hash:
            raise NotAllowed('Incorrect password')

        lifesource = bot.tool.lifesource
        self.emit(Event(self, 'portal_use', bot))
        lifesource.square.addThing(self)
        lifesource.pairWith(self)
        bot.tool = None


    @requireSquare
    def makeTool(self, ore, kind):
        """
        Make a tool out of some ore.
        """
        self._requireSameSquare(ore)

        tool = Tool(kind)
        self.emit(Event(self, 'made', tool))
        self.equip(tool)

        ls = Lifesource()
        square = ore.square
        square.removeThing(ore)
        square.addThing(ls)

        ls.pairWith(tool)
        tool.lifesource = ls


    def breakLock(self, pylon):
        """
        Break a lock on a pylon.
        """
        self._requireSameSquare(pylon)

        pylon.locks -= 1
        self.emit(Event(self, 'lock_broken', pylon))
        if pylon.locks <= 0:
            pylon.team = self.team
            pylon.locks = 1
            self.emit(Event(self, 'pylon_captured', pylon))


    def addLock(self, pylon):
        """
        Add a lock to a pylon.
        """
        self._requireSameSquare(pylon)

        pylon.locks += 1
        self.emit(Event(self, 'lock_added', pylon))



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



