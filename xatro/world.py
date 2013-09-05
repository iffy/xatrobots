from twisted.internet import defer
from twisted.python import log
import traceback

from uuid import uuid4

from collections import defaultdict
from functools import wraps

from xatro.event import Created, Destroyed, AttrSet, ItemAdded, ItemRemoved
from xatro.event import ActionPerformed
from xatro.state import State


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


    def __init__(self, event_receiver, engine=None):
        """
        @param event_receiver: Function to be called with every emitted event.
        @param engine: Game engine.
        """
        self.engine = engine
        self._state = State()
        self.objects = self._state.state
        self.event_receiver = event_receiver
        self._subscribers = defaultdict(lambda: [])
        self._receivers = defaultdict(lambda: [])
        self._on_become = defaultdict(lambda: [])
        self._on_change = defaultdict(lambda: [])
        self._on_event = defaultdict(lambda: [])


    def execute(self, action):
        """
        Execute an action according to the rules of this world's game engine.

        @param action: An L{IAction}-implementing instance.
        """
        ret = self.engine.execute(self, action)
        self.emit(ActionPerformed(action), action.emitterId())
        return ret


    def create(self, kind, receive_emissions=True):
        """
        Create an object of the given kind.

        @param receive_emissions: If C{True} then emissions from this object
            will be received by this object.  If C{False} then emissions from
            this object will not be received by this object.
        """
        obj_id = str(uuid4())
        self.emit(Created(obj_id), obj_id)
        if receive_emissions:
            # should receive own emissions
            self.subscribeTo(obj_id, self.receiverFor(obj_id))
        self.emit(AttrSet(obj_id, 'kind', kind), obj_id)
        return self.get(obj_id)


    def destroy(self, object_id):
        """
        """
        self.emit(Destroyed(object_id), object_id)
        
        # remove all functions receiving emissions from this object.
        if object_id in self._subscribers:
            self._subscribers.pop(object_id)

        # remove all functions handling events received by this object.
        if object_id in self._receivers:
            self._receivers.pop(object_id)


    def get(self, object_id):
        """
        Get an object by id.
        """
        return self.objects[object_id]


    def setAttr(self, object_id, attr_name, value):
        """
        Set the value of an object's attribute.
        """
        self.emit(AttrSet(object_id, attr_name, value), object_id)
        
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
        self.emit(ItemAdded(object_id, attr_name, value), object_id)


    def removeItem(self, object_id, attr_name, value):
        """
        Remove an item from a list.
        """
        self.emit(ItemRemoved(object_id, attr_name, value), object_id)



    # events

    def emit(self, event, object_id):
        """
        Emit an event to the world from an object.

        Functions previously supplied to L{subscribeTo} will receive
        notifications about events particular to objects.

        All events will be sent to my C{event_receiver}.
        """
        # update state
        self._state.eventReceived(event)

        try:
            self.event_receiver(event)
        except:
            log.msg('Error in event receiver %r for event %r' % (
                    self.event_receiver, event))
            log.msg(traceback.format_exc())

        for func in self._subscribers[object_id]:
            try:
                func(event)
            except:
                log.msg('Error in subscriber %r for %r for event %r' % (
                        func, object_id, event))
                log.msg(traceback.format_exc())
        
        # notify Deferreds waiting for this particular event
        events = self._on_event[(object_id, event)]
        while events:
            events.pop(0).callback(event)

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
        key = (object_id, attr_name, target)
        def _cancel(d):
            self._on_become[key].remove(d)
            if not self._on_become[key]:
                del self._on_become[key]

        d = defer.Deferred(_cancel)
        self._on_become[key].append(d)
        return d


    def onChange(self, object_id, attr_name):
        """
        Return a Deferred which will fire when the given attribute next changes.
        """
        key = (object_id, attr_name)
        def _cancel(d):
            self._on_change[key].remove(d)
            if not self._on_change[key]:
                del self._on_change[key]

        d = defer.Deferred(_cancel)
        self._on_change[key].append(d)
        return d


    def onEvent(self, object_id, event):
        """
        Return a Deferred which will fire when the given object emits the given
        event.
        """
        key = (object_id, event)
        def _cancel(d):
            self._on_event[key].remove(d)
            if not self._on_event[key]:
                del self._on_event[key]

        d = defer.Deferred(_cancel)
        self._on_event[key].append(d)
        return d





