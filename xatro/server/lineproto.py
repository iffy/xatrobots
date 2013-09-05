from twisted.internet import protocol
from twisted.protocols.basic import LineOnlyReceiver

import json


from xatro.avatar import Avatar



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



class BotLineProtocol(LineOnlyReceiver):
    """
    """

    avatar = None
    delimiter = '\r\n'


    def __init__(self, avatar):
        self.avatar = avatar


    def connectionMade(self):
        self.avatar.setEventReceiver(self.eventReceived)


    def eventReceived(self, event):
        self.sendLine(' '.join(map(str, event)))


    def connectionLost(self, reason):
        self.avatar.quit()



class BotFactory(protocol.Factory):
    """
    XXX
    """

    protocol = BotLineProtocol


    def __init__(self, world):
        self.world = world


    def buildProtocol(self, addr):
        avatar = Avatar(self.world)
        game_piece = self.world.create('bot')['id']
        avatar.setGamePiece(game_piece)

        proto = self.protocol(avatar)
        proto.factory = self
        return proto