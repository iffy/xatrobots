from twisted.trial.unittest import TestCase
from twisted.test.proto_helpers import StringTransport

from mock import MagicMock
import json

from xatro.server.lineproto import EventFeedLineFactory, EventFeedLineProtocol
from xatro.server.lineproto import EventFeedLineFactory, EventFeedLineProtocol


class EventFeedLineFactoryTest(TestCase):


    def test_LineProtocol(self):
        """
        Should make LineProtocols
        """
        self.assertEqual(EventFeedLineFactory.protocol, EventFeedLineProtocol)


    def test_trackProtocols(self):
        """
        The EventFeedLineFactory should keep track of connected protocols.
        """
        f = EventFeedLineFactory()
        p1 = f.buildProtocol(None)
        p2 = f.buildProtocol(None)
        
        self.assertNotIn(p1, f.connected_protocols)
        self.assertNotIn(p2, f.connected_protocols)

        p1.makeConnection(StringTransport())
        self.assertIn(p1, f.connected_protocols)

        p2.makeConnection(StringTransport())
        self.assertIn(p2, f.connected_protocols)

        p1.connectionLost('whatever')

        self.assertNotIn(p1, f.connected_protocols, "After a protocol "
                         "disconnects, it should not be in the connected "
                         "protocols list anymore")


    def test_eventReceived(self):
        """
        Events should be sent to all connected protocols.
        """
        f = EventFeedLineFactory()

        p = MagicMock()
        f.connected_protocols.append(p)

        f.eventReceived('hey')

        p.eventReceived.assert_called_once_with('hey')



class EventFeedLineProtocolTest(TestCase):


    def test_eventReceived(self):
        """
        An event should be written as JSON to the transport.
        """
        p = EventFeedLineProtocol()
        p.factory = MagicMock()
        t = StringTransport()
        p.makeConnection(t)

        p.eventReceived(['hey', 'ho'])
        self.assertEqual(t.value(), json.dumps(['hey', 'ho']) + '\n')




