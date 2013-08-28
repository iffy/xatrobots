from twisted.trial.unittest import TestCase


from xatro.server.event import EventRegistry


class Thing(object):
    pass



class EventRegistryTest(TestCase):


    def test_subscribe(self):
        """
        You can subscribe a function to receive an object's event notifications.
        """
        r = EventRegistry()
        self.assertEqual(len(r.receivers), 0)

        thing = Thing()
        called = []
        r.subscribe(thing, called.append)
        self.assertEqual(len(r.receivers), 1)

        del thing
        self.assertEqual(len(r.receivers), 0, "Garbage collection should cause"
                         " the receiver to not be subscribeed anymore")


    def test_notify(self):
        """
        You can notify objects' event-receiving functions.
        """
        r = EventRegistry()
        thing = Thing()
        called = []
        r.subscribe(thing, called.append)

        r.notify(thing, 'something')
        self.assertEqual(called, ['something'])


    def test_subscribeMany(self):
        """
        You can subscribe many functions to be called during notify.
        """
        r = EventRegistry()
        thing = Thing()
        c1 = []
        c2 = []
        r.subscribe(thing, c1.append)
        r.subscribe(thing, c2.append)

        r.notify(thing, 'something')
        self.assertEqual(c1, ['something'])
        self.assertEqual(c2, ['something'])


    def test_notify_nonSubscribeed(self):
        """
        Notifying for an object that hasn't been subscribeed will succeed
        silently.
        """
        r = EventRegistry()
        thing = Thing()
        r.notify(thing, 'something')


    def test_unsubscribe(self):
        """
        You can unsubscribe a receiver.
        """
        r = EventRegistry()
        thing = Thing()
        c1 = []
        r.subscribe(thing, c1.append)
        r.unsubscribe(thing, c1.append)
        r.notify(thing, 'foo')
        self.assertEqual(c1, [],
                         "Should not have called the now-unsubscribed func")

