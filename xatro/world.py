from twisted.internet import defer
from twisted.python import log
import traceback

from uuid import uuid4

from collections import defaultdict
from functools import wraps

from xatro.event import Created, Destroyed, AttrSet, ItemAdded, ItemRemoved


def memoize(f):
    # XXX make this faster if it's too slow.
    data = {}
    @wraps(f)
    def deco(*args, **kwargs):
        key = (args, tuple(kwargs.items()))
        if key in data:
            return data[key]
        data[key] = f(*args, **kwargs)
        return data[key]
    return deco



class World(object):
    """
    I am the world of a single game board.
    """


    def __init__(self, event_receiver):
        self.event_receiver = event_receiver
        self.objects = {}
        self._subscribers = defaultdict(lambda: [])
        self._receivers = defaultdict(lambda: [])
        self._on_become = defaultdict(lambda: [])
        self._on_change = defaultdict(lambda: [])


    def create(self, kind, receive_emissions=True):
        """
        Create an object of the given kind.

        @param receive_emissions: If C{True} then emissions from this object
            will be received by this object.  If C{False} then emissions from
            this object will not be received by this object.
        """
        obj_id = str(uuid4())
        obj = {
            'id': obj_id,
            'kind': kind,
        }
        self.objects[obj_id] = obj
        if receive_emissions:
            # should receive own emissions
            self.subscribeTo(obj_id, self.receiverFor(obj_id))
        self.emit(Created(obj_id), obj_id)
        self.emit(AttrSet(obj_id, 'kind', kind), obj_id)
        return obj


    def destroy(self, object_id):
        """
        """
        self.objects.pop(object_id)
        self.emit(Destroyed(object_id))


    def get(self, object_id):
        """
        Get an object by id.
        """
        return self.objects[object_id]


    def setAttr(self, object_id, attr_name, value):
        """
        Set the value of an object's attribute.
        """
        self.objects[object_id][attr_name] = value
        self.emit(AttrSet(object_id, attr_name, value))
        
        on_become = self._on_become[(object_id, attr_name, value)]
        while on_become:
            on_become.pop(0).callback(value)

        on_change = self._on_change[(object_id, attr_name)]
        while on_change:
            on_change.pop(0).callback(value)


    def addItem(self, object_id, attr_name, value):
        """
        Add an item to a list.
        """
        obj = self.objects[object_id]
        if attr_name not in obj:
            obj[attr_name] = []
        obj[attr_name].append(value)
        self.emit(ItemAdded(object_id, attr_name, value))


    def removeItem(self, object_id, attr_name, value):
        """
        Remove an item from a list.
        """
        self.objects[object_id][attr_name].remove(value)
        self.emit(ItemRemoved(object_id, attr_name, value))



    # events

    def emit(self, event, object_id=None):
        """
        Emit an event to the world.  Optionally, identify the event as coming
        from a particular object by specifying C{object_id}.  Functions
        previously supplied to L{subscribeTo} will receive notifications about
        events particular to objects.  All events will be called on my
        C{event_receiver}.
        """
        try:
            self.event_receiver(event)
        except:
            log.msg('Error in event receiver %r for event %r' % (
                    self.event_receiver, event))
            log.msg(traceback.format_exc())

        if object_id:
            for func in self._subscribers[object_id]:
                try:
                    func(event)
                except:
                    log.msg('Error in subscriber %r for %r for event %r' % (
                            func, object_id, event))
                    log.msg(traceback.format_exc())

    @memoize
    def emitterFor(self, object_id):
        """
        Get a function that will take a single argument and emit events for
        a particular object.
        """
        def f(event):
            self.emit(event, object_id)
        return f


    def subscribeTo(self, object_id, callback):
        """
        Subscribe to the events emitted by the given object.
        """
        self._subscribers[object_id].append(callback)


    def unsubscribeFrom(self, object_id, callback):
        """
        Unsubscribe from the events emitted by the given object.
        """
        self._subscribers[object_id].remove(callback)


    def eventReceived(self, event, object_id):
        """
        Receive an event for a particular object.
        """
        for func in self._receivers[object_id]:
            func(event)


    @memoize
    def receiverFor(self, object_id):
        """
        Get a function that will take a single argument and call
        L{eventReceived} for the given object.
        """
        def f(event):
            self.eventReceived(event, object_id)
        return f


    def receiveFor(self, object_id, callback):
        """
        Subscribe to the events received by the given object.
        """
        self._receivers[object_id].append(callback)


    def stopReceivingFor(self, object_id, callback):
        """
        Unsubscribe from the events received by the given object.
        """
        self._receivers[object_id].remove(callback)



    # change notifications


    def onBecome(self, object_id, attr_name, target):
        """
        Return a Deferred which will fire when the given attribute becomes
        the given value.
        """
        def _cancel(d):
            self._on_become[(object_id, attr_name, target)].remove(d)

        d = defer.Deferred(_cancel)
        self._on_become[(object_id, attr_name, target)].append(d)
        return d


    def onChange(self, object_id, attr_name):
        """
        Return a Deferred which will fire when the given attribute next changes.
        """
        def _cancel(d):
            self._on_change[(object_id, attr_name)].remove(d)

        d = defer.Deferred(_cancel)
        self._on_change[(object_id, attr_name)].append(d)
        return d





