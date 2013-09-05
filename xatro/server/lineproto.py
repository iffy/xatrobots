from twisted.internet import protocol
from twisted.protocols.basic import LineOnlyReceiver

import json

from xatro.transformer import ToStringTransformer
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
        self.event_transformer = ToStringTransformer()


    def connectionMade(self):
        self.avatar.setEventReceiver(self.eventReceived)


    def eventReceived(self, event):
        self.sendLine(self.event_transformer.transform(event))


    def connectionLost(self, reason):
        self.avatar.quit()


    def lineReceived(self, line):
        # XXX this is really fragile, but hey... it's okay for a demo.
        parts = line.split(' ')
        cmd_name = parts[0]
        cmd_cls = self.avatar.availableCommands()[cmd_name.lower()]
        self.avatar.execute(cmd_cls, *parts[1:])



class BotFactory(protocol.Factory):
    """
    XXX
    """

    protocol = BotLineProtocol


    def __init__(self, world, commands=None):
        self.world = world
        self.commands = commands


    def buildProtocol(self, addr):
        avatar = Avatar(self.world, self.commands)
        game_piece = self.world.create('bot')['id']
        avatar.setGamePiece(game_piece)

        proto = self.protocol(avatar)
        proto.factory = self
        return proto



