from twisted.python import log

from xatro.event import Created, Destroyed, AttrSet, ItemAdded, ItemRemoved
from xatro.router import Router



class State(object):
    """
    I hold the state of a world as built up by events.

    @ivar state: Dictionary of all the objects in the world.
    """

    router = Router()


    def __init__(self):
        self.state = {}


    def eventReceived(self, event):
        log.msg(event)
        try:
            return self.router.call(event.__class__, event)
        except KeyError:
            pass


    @router.handle(Created)
    def handle_Created(self, event):
        self.state[event.id] = {
            'id': event.id,
        }


    @router.handle(Destroyed)
    def handle_Destroyed(self, event):
        self.state.pop(event.id)


    @router.handle(AttrSet)
    def handle_AttrSet(self, (id, name, value)):
        self.state[id][name] = value


    @router.handle(ItemAdded)
    def handle_ItemAdded(self, (id, name, value)):
        obj = self.state[id]
        if name not in obj:
            obj[name] = []
        obj[name].append(value)


    @router.handle(ItemRemoved)
    def handle_ItemRemoved(self, (id, name, value)):
        self.state[id][name].remove(value)