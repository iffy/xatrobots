
from zope.interface import implements
from xatro.interface import IAction

from xatro.event import Destroyed



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



def _receiveEnergy(world, obj_id, energy_id):
    """
    Receive energy, and appropriately watch for the energy's destruction.
    """
    # give this thing some energy
    world.addItem(obj_id, 'energy', energy_id)

    # wait for it to be destroyed
    d = world.onEvent(energy_id, Destroyed(energy_id))
    d.addCallback(_rmFromEnergyPool, world, obj_id)
    world.setAttr(energy_id, 'onDestroy', d)


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


    def _rmFromEnergy(self, ev, world, thing_id):
        """
        Remove energy from a thing's list of energy.
        """
        


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
            e_obj = world.get(e)
            e_obj['onDestroy'].cancel()

            # add to receiver (and subscribe to energy destruction)
            world.addItem(receiver_id, 'energy', e)
            d = world.onEvent(e, Destroyed(e))
            d.addCallback(self._rmFromEnergy, world, receiver_id)
            world.setAttr(e, 'onDestroy', d)


    def _rmFromEnergy(self, ev, world, thing_id):
        """
        Remove energy from a thing's list of energy.
        """
        world.removeItem(thing_id, 'energy', ev.id)


# ChargeBattery()
# ShareEnergy(who, amount)
# _ConsumeEnergy(amount)

# MakeTool(ore, kind_of_tool)
# Shoot(what, energy)
# Repair(what, energy)
# OpenPortal(code)
# UsePortal(code)
# Look(eyes)
# Status(thing)

# AddLock(portal)
# BreakLock(portal)



class MakeTool(object):


    def __init__(self, bot, ore, tool):
        self.bot = bot
        self.ore = ore
        self.tool = tool


    def execute(self, world):
        pass
