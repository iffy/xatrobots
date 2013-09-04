from twisted.internet import defer

from uuid import uuid4

from collections import defaultdict

from xatro.event import Created, Destroyed, AttrSet, ItemAdded, ItemRemoved



class World(object):
    """
    I am the world of a single game board.
    """


    def __init__(self, event_receiver):
        self.event_receiver = event_receiver
        self.objects = {}
        self._subscribers = defaultdict(lambda: [])
        self._on_become = defaultdict(lambda: [])
        self._on_change = defaultdict(lambda: [])


    def emit(self, event, object_id=None):
        """
        Emit an event to the world.  Optionally, identify the event as coming
        from a particular object by specifying C{object_id}.
        """
        self.event_receiver(event)
        if object_id:
            for func in self._subscribers[object_id]:
                func(event)


    def create(self, kind):
        """
        Create an object of the given kind.
        """
        obj_id = str(uuid4())
        obj = {
            'id': obj_id,
            'kind': kind,
        }
        self.objects[obj_id] = obj
        self.emit(Created(obj_id))
        self.emit(AttrSet(obj_id, 'kind', kind))
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





