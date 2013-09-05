from twisted.internet import protocol
from twisted.protocols.basic import LineOnlyReceiver

import json



class EventFeedLineProtocol(LineOnlyReceiver):
    """
    XXX
    """

    delimiter = '\n'


    def connectionMade(self):
        self.factory.connected_protocols.append(self)


    def connectionLost(self, reason):
        """
        XXX
        """
        self.factory.connected_protocols.remove(self)


    def eventReceived(self, event):
        """
        XXX
        """
        self.sendLine(json.dumps(event))



class EventFeedLineFactory(protocol.Factory):
    """
    XXX
    """

    protocol = EventFeedLineProtocol


    def __init__(self):
        self.connected_protocols = []


    def eventReceived(self, event):
        """
        """
        for p in self.connected_protocols:
            p.eventReceived(event)


