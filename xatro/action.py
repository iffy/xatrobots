


class Move(object):


    def __init__(self, thing, dst):
        self.thing = thing
        self.dst = dst


    def execute(self, world):
        thing = self.thing
        dst = self.dst

        # tell them about each other
        world.setAttr(thing, 'location', dst)
        world.addItem(dst, 'contents', thing)

        # subscribe to the appropriate events
        world.subscribeTo(dst, world.receiverFor(dst))
        world.subscribeTo(dst, world.receiverFor(thing))
        world.subscribeTo(thing, world.receiverFor(dst))
        world.subscribeTo(thing, world.receiverFor(thing))



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