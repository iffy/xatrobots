from twisted.python import log

from xatro.event import Created, Destroyed, AttrSet, ItemAdded, ItemRemoved
from xatro.transformer import Mapper



class State(object):
    """
    I hold the state of a world as built up by events.

    @ivar state: Dictionary of all the objects in the world.
    """

    mapper = Mapper()


    def __init__(self):
        self.state = {}


    def eventReceived(self, event):
        log.msg(event)
        try:
            return self.mapper.call(event.__class__, event)
        except KeyError:
            pass


    @mapper.handle(Created)
    def handle_Created(self, event):
        self.state[event.id] = {
            'id': event.id,
        }


    @mapper.handle(Destroyed)
    def handle_Destroyed(self, event):
        self.state.pop(event.id)


    @mapper.handle(AttrSet)
    def handle_AttrSet(self, (id, name, value)):
        self.state[id][name] = value


    @mapper.handle(ItemAdded)
    def handle_ItemAdded(self, (id, name, value)):
        obj = self.state[id]
        if name not in obj:
            obj[name] = []
        obj[name].append(value)


    @mapper.handle(ItemRemoved)
    def handle_ItemRemoved(self, (id, name, value)):
        self.state[id][name].remove(value)