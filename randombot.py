from twisted.protocols import amp
from twisted.internet import endpoints, reactor, defer, task
from xatro.server.amp import Identify, ReceiveEvent, WorldCommand
from twisted.python import log

from uuid import uuid4
import json
import random



class DeferredBroadcaster(object):


    def __init__(self):
        self._has_value = False
        self._value = None
        self._pending = []


    def get(self):
        if self._has_value:
            return defer.succeed(self._value)
        d = defer.Deferred()
        self._pending.append(d)
        return d


    def callback(self, val):
        self._has_value = True
        self._value = val
        while self._pending:
            self._pending.pop(0).callback(val)



class RandomBot(object):

    protocol = None
    state = 'init'

    id = None
    team = None
    team_password = None
    energy = 0
    hp = None
    tool = None

    current_square = None
    visible_things = None

    endpoint = None
    reactor = None


    def __init__(self, firstone=False, friendlies=None):
        self.firstone = firstone
        self.things = {}
        self.friendlies = friendlies or []

        self.identity = DeferredBroadcaster()
        self.identity.get().addCallback(lambda _:self.tryToLand())
        
        self.portal = DeferredBroadcaster()
        self.squares = DeferredBroadcaster()


    def x(self, name, args=None, work=None):
        args = [self.encode(x) for x in (args or [])]
        return self.protocol.executeWorldCommand(name, args, work)


    def encode(self, x):
        if type(x) == unicode:
            return x.encode('utf-8')
        return x

    
    def gotIdentity(self, id):
        print 'got identitiy'
        self.id = id
        self.friendlies.append(id)
        self.identity.callback(id)
        self.listSquares()


    @defer.inlineCallbacks
    def joinTeam(self):
        # maybe create the team
        if self.team is None:
            self.team = str(uuid4()) + 'RANDOMTEAM'
            self.team_password = str(uuid4()) + 'PASSWORD'
            yield self.x('createteam', [self.team, self.team_password])

        # join the team
        yield self.x('jointeam', [self.team, self.team_password])


    @defer.inlineCallbacks
    def listSquares(self):
        squares = yield self.x('listsquares')
        self.squares.callback(squares)


    @defer.inlineCallbacks
    def tryToLand(self):
        yield self.joinTeam()
        if self.firstone:
            yield self.landWithoutPortal()
        else:
            yield self.landWithPortal()
        self.landed()


    @defer.inlineCallbacks
    def landWithoutPortal(self):
        # wait for squares to be listed
        squares = yield self.squares.get()

        # choose a square
        square = random.choice(squares)
        yield self.x('move', [square['id']])
        self.current_square = square


    @defer.inlineCallbacks
    def landWithPortal(self):
        # wait for portal to open
        portal = yield self.portal.get()
        yield self.x('useportal', [portal])


    def eventReceived(self, ev):
        ev = json.loads(ev)
        if ev.get('id') == self.id:
            return self.selfEventReceived(ev)


    def selfEventReceived(self, ev):
        if ev['ev'] == 'attrset':
            if ('created_energy', 0) == (ev['name'], ev['value']):
                # it's time to charge again
                self.charge()
            elif ev['name'] == 'hp':
                self.hp = ev['value']
                if self.hp == 0:
                    self.protocol.transport.loseConnection()
        elif ev['ev'] == 'itemadded':
            if ev['name'] == 'energy':
                self.energy += 1
        elif ev['ev'] == 'itemremoved':
            if ev['name'] == 'energy':
                self.energy -= 1


    def landed(self):
        """
        I've landed.  Start shootin!
        """
        # start the charging cycle
        self.charge()

        # start the random state machine
        self.state = 'justarrived'

        self.lc = task.LoopingCall(self.doCycle)
        self.lc.start(0.2)


    def charge(self):
        self.x('charge')


    
    # state machine


    def doCycle(self):
        handler = getattr(self, 'state_' + self.state, lambda:None)
        try:
            return handler()
        except Exception as e:
            print e


    def state_bored(self):
        """
        I need an activity.
        """
        possible_activities = ['move']
        if self.unexaminedThings():
            possible_activities.append('examine')
        
        if self.energy and self.targetsFor('share'):
            possible_activities.append('share')

        if self.targetsFor('maketool'):
            possible_activities.append('maketool')

        if self.targetsFor('summon'):
            possible_activities.append('summon')
        
        if self.tool == 'cannon' and self.targetsFor('shoot'):
            possible_activities.append('shoot')

        if self.tool == 'wrench' and self.targetsFor('repair'):
            possible_activities.append('repair')

        activity = random.choice(possible_activities)
        #print "I'm going to %s" % (activity,)
        return self.doActivity(activity)


    def targetsFor(self, activity):
        return {
            'share': lambda: self.visibleX(['bot'], [self.id], self.friendlies),
            'maketool': lambda: self.visibleX(['ore']),
            'shoot': lambda: self.visibleX(['bot', 'lifesource'], self.friendlies),
            'repair': lambda: self.visibleX(['bot', 'lifesource'], including=self.friendlies),
            'summon': lambda: self.visibleX(['ore']),
        }.get(activity, lambda:[])()


    @defer.inlineCallbacks
    def state_justarrived(self):
        yield self.doActivity('look')
        self.state = 'bored'


    # activities


    def doActivity(self, activity):
        handler = getattr(self, 'do_' + activity, lambda:None)
        try:
            return handler()
        except Exception as e:
            print e


    @defer.inlineCallbacks
    def do_look(self):
        try:
            stuff = yield self.x('look', [])
            self.visible_things = [x.encode('utf-8') for x in stuff]
        except Exception as e:
            print e


    @defer.inlineCallbacks
    def do_move(self):
        squares = yield self.squares.get()
        adjacent_squares = [x for x in squares if self._isAdjacent(x)]
        if not adjacent_squares:
            return
        square = random.choice(adjacent_squares)
        try:
            yield self.x('move', [square['id']])
        except Exception as e:
            print e
        self.current_square = square
        yield self.do_look()


    def _isAdjacent(self, square):
        c = square.get('coordinates', (0,0))
        my_c = self.current_square.get('coordinates', (0,0))
        distance = abs(c[0] - my_c[0]) + abs(c[1] - my_c[1])
        return distance == 1


    @defer.inlineCallbacks
    def do_examine(self):
        """
        Look at something to identify it.
        """
        target = random.choice(self.unexaminedThings())
        try:
            result = yield self.x('lookat', [target])
            self.things[target] = result
        except Exception as e:
            print e


    def visibleX(self, kinds, excluding=None, including=None):
        """
        Return an iterable of ids of visible things of the given kind.
        """
        excluding = excluding or []
        including = including or []
        pool = set(self.visible_things)
        if including:
            pool = pool & set(including)
        ret = []
        for id in (x for x in pool if x not in excluding):
            thing = self.things.get(id, {})
            if thing.get('kind') in kinds:
                ret.append(id)
        return ret


    def unexaminedThings(self):
        """
        Return a list of the unexamined ids I can see.
        """
        return list(set(self.visible_things) - set(self.things))


    @defer.inlineCallbacks
    def do_share(self):
        print 'sharing', self.energy
        target = random.choice(self.targetsFor('share'))
        try:
            yield self.x('share', [target, str(self.energy)])
        except Exception as e:
            print e


    @defer.inlineCallbacks
    def do_maketool(self):
        tool = random.choice(['cannon', 'wrench'])
        ore = random.choice(self.targetsFor('maketool'))
        try:
            yield self.x('maketool', [ore, tool])
            self.tool = tool
        except Exception as e:
            self.things.pop(ore)
            print e


    @defer.inlineCallbacks
    def do_shoot(self):
        target = random.choice(self.targetsFor('shoot'))
        amount = '1'
        if self.energy == 3:
            amount = '6'
        elif self.energy == 2:
            amount = '3'
        try:
            yield self.x('shoot', [target, amount])
        except Exception as e:
            print e


    @defer.inlineCallbacks
    def do_repair(self):
        target = random.choice(self.targetsFor('repair'))
        amount = '1'
        if self.energy == 3:
            amount = '6'
        elif self.energy == 2:
            amount = '3'
        try:
            yield self.x('repair', [target, amount])
        except Exception as e:
            print e


    @defer.inlineCallbacks
    def do_summon(self):
        """
        Summon another bot to help
        """
        # make another bot join
        bot = RandomBot(firstone=False, friendlies=self.friendlies)
        bot.things = self.things
        bot.team = self.team
        bot.team_password = self.team_password
        protocol = ClientProtocol(bot)
        bot.protocol = protocol
        bot.endpoint = self.endpoint
        bot.reactor = self.reactor

        endpoint = endpoints.clientFromString(self.reactor, self.endpoint)
        p = endpoints.connectProtocol(endpoint, protocol)

        # once they have an identity, make them a portal
        new_id = yield bot.identity.get()
        ore = random.choice(self.targetsFor('summon'))
        try:
            yield self.x('openportal', [ore, new_id])
        except Exception as e:
            print 'error opening portal'
            print e
            self.things.pop(ore)
            protocol.transport.loseConnection()

        # XXX this is odd
        bot.current_square = self.current_square
        
        # portal is made, tell the other bot to join it.
        bot.portal.callback(ore)


    






class ClientProtocol(amp.AMP):


    def __init__(self, brains):
        self.brains = brains
        self.done = defer.Deferred()


    @Identify.responder
    def identify(self, id):
        self.brains.gotIdentity(id)
        return {}

    @ReceiveEvent.responder
    def eventReceived(self, ev):
        self.brains.eventReceived(ev)
        return {}


    def executeWorldCommand(self, name, args, work=None):
        d = self.callRemote(WorldCommand, name=name, args=args, work=work)
        d.addCallback(lambda d: json.loads(d['data']))
        return d


    def connectionLost(self, reason):
        self.done.callback(self)




def main(reactor, str_endpoint):
    bot = RandomBot(firstone=True)
    protocol = ClientProtocol(bot)
    bot.protocol = protocol
    bot.endpoint = str_endpoint
    bot.reactor = reactor
    
    endpoint = endpoints.clientFromString(reactor, str_endpoint)
    p = endpoints.connectProtocol(endpoint, protocol)
    return p.addCallback(lambda _: protocol.done)


if __name__ == '__main__':
    import sys
    log.startLogging(sys.stdout)
    str_endpoint = sys.argv[1]
    task.react(main, [str_endpoint])