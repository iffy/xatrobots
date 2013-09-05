


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



class Charge(object):


    def __init__(self, bot):
        self.bot = bot


    def execute(self, world):
        pass