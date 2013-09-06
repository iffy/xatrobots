from twisted.internet import defer
from twisted.python import log
import traceback

from uuid import uuid4

from collections import defaultdict
from functools import wraps
from weakref import WeakKeyDictionary

from xatro.event import Created, Destroyed, AttrSet, ItemAdded, ItemRemoved
from xatro.event import ActionPerformed, AttrDel
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
        self._event_queue = []
        self._event_queue_running = False
        self._envelopes = WeakKeyDictionary()
        self._world_envelopes = {}
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
        event = ActionPerformed(action)
        for object_id in action.emitters():
            self.emit(event, object_id)
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


    def delAttr(self, object_id, attr_name):
        """
        Delete an attribute from an object.
        """
        self.emit(AttrDel(object_id, attr_name), object_id)


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
        self._event_queue.append((event, object_id))

        if self._event_queue_running:
            # we'll get to it when the current event is done being processed.
            return

        self._event_queue_running = True
        called_list = []
        while self._event_queue:
            event, object_id = self._event_queue.pop(0)
            
            # update state
            self._state.eventReceived(event)

            try:
                self._callOnce(called_list, self.event_receiver, event)
            except:
                log.msg('Error in event receiver %r for event %r' % (
                        self.event_receiver, event))
                log.msg(traceback.format_exc())

            for func in self._subscribers[object_id]:
                try:
                    self._callOnce(called_list, func, event)
                except:
                    log.msg('Error in subscriber %r for %r for event %r' % (
                            func, object_id, event))
                    log.msg(traceback.format_exc())
            
            # notify Deferreds waiting for this particular event
            events = self._on_event[(object_id, event)]
            while events:
                events.pop(0).callback(event)
        self._event_queue_running = False


    def _callOnce(self, called_list, func, *args, **kwargs):
        """
        Call the given function with the given arguments only once,
        using C{called_list} as the memory for which functions have been
        called.
        """
        key = (func, args, kwargs)
        if key in called_list:
            return
        called_list.append(key)
        func(*args, **kwargs)


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


    def onNextChange(self, object_id, attr_name):
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


    # envelopes


    def envelope(self, obj):
        """
        Get the envelope associated with an object (or create one).  This is a
        way of associating attributes with an object without setting the
        attributes on the object itself.  This may be a really bad idea :)

        If C{obj} is the id of an object in the world (made with L{create})
        then the envelope will only exist as long as the object exists and can
        only be created if the object has been created.
        """
        if type(obj) == str:
            # world object, not a python object
            return self._worldEnvelope(obj)

        # object envelopes
        envelopes = self._envelopes
        if obj not in envelopes:
            envelopes[obj] = {}
        return envelopes[obj]


    def _worldEnvelope(self, key):
        if key not in self._world_envelopes:
            # only ids for objects in the world are allowed
            if key not in self.objects:
                raise KeyError(key)

            self._world_envelopes[key] = {}
            
            # watch for destruction
            d = self.onEvent(key, Destroyed(key))
            d.addCallback(lambda _,key: self._destroyWorldEnvelope(key), key)
        return self._world_envelopes[key]


    def _destroyWorldEnvelope(self, key):
        self._world_envelopes.pop(key)





