


class Move(object):
    """
    Move an object from where it is to a new location.
    """


    def __init__(self, thing, dst):
        """
        @param thing: An object id.
        @param dst: A location object id.
        """
        self.thing = thing
        self.dst = dst


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



class Charge(object):
    """
    Create some energy.
    """

    def __init__(self, thing):
        self.thing = thing


    def execute(self, world):
        thing_id = self.thing

        e = world.create('energy')
        world.setAttr(e['id'], 'creator', thing_id)

        thing = world.get(thing_id)

        # give this thing some energy
        world.addItem(thing_id, 'energy', e['id'])

        # record that this thing created energy
        world.setAttr(thing_id, 'created_energy',
                      thing.get('created_energy', 0) + 1)



class ShareEnergy(object):
    """
    Share energy with someone else.
    """

    def __init__(self, giver, receiver, amount):
        self.giver = giver
        self.receiver = receiver
        self.amount = amount


    def execute(self, world):
        """
        """
        giver_id = self.giver
        giver = world.get(giver_id)

        e = giver['energy'].pop(0)



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
