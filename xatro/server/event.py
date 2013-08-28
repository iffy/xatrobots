from collections import namedtuple
from weakref import WeakKeyDictionary


Event = namedtuple('Event', ['subject', 'verb', 'object'])



class EventRegistry(object):
    """
    I compose event handling for objects
    """


    def __init__(self):
        self.receivers = WeakKeyDictionary()


    def subscribe(self, obj, receiver):
        """
        Register a function to be called when C{obj} gets events.
        """
        if obj not in self.receivers:
            self.receivers[obj] = []
        self.receivers[obj].append(receiver)


    def unsubscribe(self, obj, receiver):
        """
        Unregister a function from receiving notifications for an obj.
        """
        self.receivers[obj].remove(receiver)


    def notify(self, obj, event):
        for r in self.receivers.get(obj, []):
            r(event)