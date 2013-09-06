from twisted.internet import defer
from zope.interface import implements

from collections import defaultdict

from xatro.interface import IAction
from xatro.event import Destroyed
from xatro.error import NotEnoughEnergy, Invulnerable, NotAllowed



class Move(object):
    """
    Move an object from where it is to a new location.
    """

    implements(IAction)


    def __init__(self, thing, dst):
        """
        @param thing: An object id.
        @param dst: A location object id.
        """
        self.thing = thing
        self.dst = dst


    def emitters(self):
        return [self.thing]


    def execute(self, world):
        thing = self.thing
        dst = self.dst

        if dst is not None:
            if dst not in world.objects:
                raise NotAllowed(dst)

        thing_obj = world.get(thing)
        old_location_id = thing_obj.get('location')
        if old_location_id:
            # remove from previous location
            world.removeItem(old_location_id, 'contents', thing)

            # unsubscribe previous location events
            world.unsubscribeFrom(old_location_id, world.receiverFor(thing))
            world.unsubscribeFrom(thing, world.receiverFor(old_location_id))

        # tell the thing where it is
        world.setAttr(thing, 'location', dst)

        if dst:
            # tell the room it has a new lodger
            world.addItem(dst, 'contents', thing)

            # subscribe location and thing to each other's events
            world.subscribeTo(dst, world.receiverFor(thing))
            world.subscribeTo(thing, world.receiverFor(dst))

            # location should emit what it receives
            world.receiveFor(dst, world.emitterFor(dst))



class Look(object):
    """
    Look at the surroundings.
    """

    implements(IAction)


    def __init__(self, thing):
        self.thing = thing


    def emitters(self):
        return [self.thing]


    def execute(self, world):
        """
        """
        location = world.get(self.thing).get('location')
        if location:
            return world.get(location)['contents']
        return []


def _ignoreCancellation(err):
    err.trap(defer.CancelledError)


def _receiveEnergy(world, obj_id, energy_id):
    """
    Receive energy, and appropriately watch for the energy's destruction.
    """
    # give this thing some energy
    world.addItem(obj_id, 'energy', energy_id)

    # wait for it to be destroyed
    d = world.onEvent(energy_id, Destroyed(energy_id))
    d.addCallback(_rmFromEnergyPool, world, obj_id)
    d.addErrback(_ignoreCancellation)
    world.envelope(energy_id)['_onDestroy'] = d


def _rmFromEnergyPool(ev, world, obj_id):
    """
    Remove energy from an object's energy pool.
    """
    world.removeItem(obj_id, 'energy', ev.id)



class Charge(object):
    """
    Create some energy.
    """

    implements(IAction)


    def __init__(self, thing):
        self.thing = thing


    def emitters(self):
        return [self.thing]


    def execute(self, world):
        thing_id = self.thing

        e = world.create('energy')

        thing = world.get(thing_id)

        _receiveEnergy(world, thing_id, e['id'])

        # record that this thing created energy
        world.setAttr(thing_id, 'created_energy',
                      thing.get('created_energy', 0) + 1)

        # wait for it to be destroyed
        d = world.onEvent(e['id'], Destroyed(e['id']))
        d.addCallback(self._decCreatedEnergy, world, thing_id)

        # destroy the energy when the creator is dead
        # XXX this might be ripped out of here and put in the game engine
        d = world.onBecome(thing_id, 'location', None)
        d.addCallback(lambda x:world.destroy(e['id']))


    def _decCreatedEnergy(self, ev, world, thing_id):
        """
        Decrement the created_energy amount of a thing.
        """
        world.setAttr(thing_id, 'created_energy',
                      world.get(thing_id)['created_energy'] - 1)



class ShareEnergy(object):
    """
    Share some energy.
    """

    implements(IAction)


    def __init__(self, giver, receiver, amount):
        self.giver = giver
        self.receiver = receiver
        self.amount = amount


    def emitters(self):
        return [self.giver, self.receiver]


    def execute(self, world):
        """
        """
        giver_id = self.giver
        receiver_id = self.receiver
        amount = self.amount

        # get some energy
        giver = world.get(giver_id)

        for e in giver['energy'][:amount]:
            # remove from giver (and unsubscribe from energy destruction)
            world.removeItem(giver_id, 'energy', e)
            world.envelope(e)['_onDestroy'].cancel()

            # add to receiver (and subscribe to energy destruction)
            _receiveEnergy(world, receiver_id, e)



class ConsumeEnergy(object):
    """
    Consume some energy.
    """

    implements(IAction)

    def __init__(self, thing, amount):
        self.thing = thing
        self.amount = amount


    def emitters(self):
        return [self.thing]


    def execute(self, world):
        """
        Consume energy.

        @raise NotEnoughEnergy: If there's not enough energy.
        """
        thing = world.get(self.thing)
        if len(thing['energy']) < self.amount:
            raise NotEnoughEnergy(self.amount)

        for e in thing['energy'][:self.amount]:
            world.destroy(e)



class Shoot(object):
    """
    Shoot something.
    """

    implements(IAction)

    def __init__(self, shooter, target, damage):
        self.shooter = shooter
        self.target = target
        self.damage = damage


    def emitters(self):
        return [self.shooter, self.target]


    def execute(self, world):
        """
        @raise Invulnerable: If the target can't be shot.
        """
        target = world.get(self.target)
        
        if target.get('hp') is None:
            raise Invulnerable(self.target)

        new_hp = max(target['hp'] - self.damage, 0)
        world.setAttr(target['id'], 'hp', new_hp)



class Repair(object):
    """
    Repair something
    """

    implements(IAction)

    def __init__(self, repairman, target, amount):
        self.repairman = repairman
        self.target = target
        self.amount = amount


    def emitters(self):
        return [self.repairman, self.target]


    def execute(self, world):
        """
        @raise Invulnerable: If the target can't be repaired.
        """
        target = world.get(self.target)
        
        if target.get('hp') is None:
            raise Invulnerable(self.target)

        new_hp = target['hp'] + self.amount
        world.setAttr(target['id'], 'hp', new_hp)



class MakeTool(object):

    implements(IAction)


    def __init__(self, thing, ore, tool):
        self.thing = thing
        self.ore = ore
        self.tool = tool


    def emitters(self):
        return [self.thing, self.ore]


    def execute(self, world):
        ore = world.get(self.ore)
        if ore['kind'] != 'ore':
            raise NotAllowed('%s is not ore' % (self.ore,))

        world.setAttr(self.ore, 'kind', 'lifesource')
        world.setAttr(self.thing, 'tool', self.tool)

        # destroy the tool when the creator is dead
        d = world.onBecome(self.thing, 'location', None)
        d.addCallback(self._revert, world, self.thing, self.ore)

        # destroy when lifesource is dead
        d = world.onBecome(self.ore, 'hp', 0)
        d.addCallback(self._revert, world, self.thing, self.ore)


    def _revert(self, ev, world, thing_id, ore_id):
        world.delAttr(thing_id, 'tool')
        world.setAttr(ore_id, 'kind', 'ore')



class OpenPortal(object):


    implements(IAction)


    def __init__(self, thing, ore, user):
        self.thing = thing
        self.ore = ore
        self.user = user


    def emitters(self):
        return [self.thing, self.user]


    def execute(self, world):
        """
        Open a portal for another bot.
        """
        world.setAttr(self.ore, 'kind', 'portal')
        world.setAttr(self.ore, 'portal_user', self.user)

        # watch for the death of the opener
        d = world.onBecome(self.thing, 'location', None)
        d.addCallback(self._revert, world, self.ore)
        d.addErrback(_ignoreCancellation)
        world.envelope(self.ore)['_onOpenerDeath'] = d


    def _revert(self, ev, world, ore_id):
        world.setAttr(ore_id, 'kind', 'ore')
        world.delAttr(ore_id, 'portal_user')



class UsePortal(object):
    """
    Use a portal to land in the location that the portal is in.
    """

    implements(IAction)


    def __init__(self, thing, portal):
        self.thing = thing
        self.portal = portal


    def emitters(self):
        return [self.thing]


    def execute(self, world):
        portal = world.get(self.portal)

        # make sure the portal is for this user
        if portal['portal_user'] != self.thing:
            raise NotAllowed('Portal is for %s' % (portal['portal_user'],))

        Move(self.thing, portal['location']).execute(world)

        # watch for destruction of portal
        d = world.onEvent(self.portal, Destroyed(self.portal))
        d.addCallback(self._killUser, world, self.thing)

        # watch for death of portal
        d = world.onBecome(self.portal, 'hp', 0)
        d.addCallback(self._revert, world, self.portal, self.thing)

        # stop watching for the death of the owner
        world.envelope(self.portal)['_onOpenerDeath'].cancel()


    def _killUser(self, ev, world, thing):
        Move(thing, None).execute(world)


    def _revert(self, ev, world, ore_id, thing):
        self._killUser(ev, world, thing)
        world.setAttr(ore_id, 'kind', 'ore')
        world.delAttr(ore_id, 'portal_user')



class ListSquares(object):
    """
    List the squares in the world.
    """

    implements(IAction)


    def __init__(self, eyes):
        self.eyes = eyes


    def emitters(self):
        return []


    def execute(self, world):
        """
        List the squares in the world.
        """
        # XXX optimize this if it's too slow.  It's very possible that it's
        # too slow.
        ret = []
        squares = (x for x in world.objects.values() if x['kind'] == 'square')
        for square in squares:
            contents = defaultdict(lambda: 0)
            for thing_id in square.get('contents', []):
                thing = world.get(thing_id)
                contents[thing['kind']] += 1
            ret.append({
                'id': square['id'],
                'kind': square['kind'],
                'coordinates': square.get('coordinates'),
                'contents': contents,
            })
        return ret



class AddLock(object):
    """
    Add a lock to something
    """

    implements(IAction)


    def __init__(self, doer, target):
        self.doer = doer
        self.target = target


    def emitters(self):
        return [self.doer, self.target]


    def execute(self, world):
        target = world.get(self.target)
        world.setAttr(target['id'], 'locks', target.get('locks', 0) + 1)



class BreakLock(object):
    """
    Remove a lock from something
    """

    implements(IAction)


    def __init__(self, doer, target):
        self.doer = doer
        self.target = target


    def emitters(self):
        return [self.doer, self.target]


    def execute(self, world):
        target = world.get(self.target)
        new_locks = max(target.get('locks', 0) - 1, 0)
        world.setAttr(target['id'], 'locks', new_locks)



class CreateTeam(object):
    """
    Create a team with a password.
    """

    implements(IAction)


    def __init__(self, creator, team_name, password):
        self.creator = creator
        self.team_name = team_name
        self.password = password


    def emitters(self):
        return []


    def execute(self, world):
        return world.auth.createEntity(self.team_name, self.password)



class JoinTeam(object):
    """
    Join a team.
    """

    implements(IAction)


    def __init__(self, thing, team_name, password):
        self.thing = thing
        self.team_name = team_name
        self.password = password


    def emitters(self):
        return [self.thing]


    def execute(self, world):
        d = world.auth.checkPassword(self.team_name, self.password)
        d.addCallback(self._setTeam, world, self.thing)
        return d


    def _setTeam(self, team, world, thing):
        world.setAttr(thing, 'team', team)



