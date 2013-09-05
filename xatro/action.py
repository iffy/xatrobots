


class Move(object):


    def __init__(self, thing, dst):
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
            world.unsubscribeFrom(old_location_id, world.receiverFor(thing))
            world.unsubscribeFrom(thing, world.receiverFor(old_location_id))

        # tell them about each other
        world.setAttr(thing, 'location', dst)
        world.addItem(dst, 'contents', thing)

        # subscribe to the appropriate events
        world.subscribeTo(dst, world.receiverFor(thing))
        world.subscribeTo(thing, world.receiverFor(dst))



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