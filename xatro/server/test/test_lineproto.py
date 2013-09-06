from twisted.trial.unittest import TestCase
from twisted.test.proto_helpers import StringTransport
from twisted.internet import defer

from mock import MagicMock, create_autospec
import json

from xatro.server.lineproto import EventFeedLineFactory, EventFeedLineProtocol
from xatro.server.lineproto import BotFactory, BotLineProtocol

from xatro.world import World
from xatro.avatar import Avatar
from xatro.event import AttrSet
from xatro.action import Move
from xatro.transformer import ToStringTransformer



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




class BotFactoryTest(TestCase):


    def test_BotLineProtocol(self):
        self.assertEqual(BotFactory.protocol, BotLineProtocol)


    def test_init(self):
        """
        A factory should know about the world.
        """
        f = BotFactory('world')
        self.assertEqual(f.world, 'world')


    def test_buildProtocol(self):
        """
        When a protocol is made, the protocol should be given an Avatar
        that is connected to a 'bot' in the world.  Also, the avatar should be
        given a copy of the available commands.
        """
        world = World(MagicMock())
        f = BotFactory(world, {'foo': 'bar'})
        proto = f.buildProtocol(None)
        self.assertEqual(proto.factory, f)
        self.assertTrue(isinstance(proto, BotLineProtocol))
        self.assertTrue(isinstance(proto.avatar, Avatar))
        self.assertEqual(proto.avatar._world, world, "Should be connected to "
                         "the world")
        self.assertNotEqual(proto.avatar._game_piece, None, "Should have a game"
                            " piece")
        self.assertEqual(proto.avatar.availableCommands(), {'foo': 'bar'})
        obj = world.get(proto.avatar._game_piece)
        self.assertEqual(obj['kind'], 'bot', "Should make a bot in the world")

        self.assertTrue(isinstance(proto.event_transformer,
                        ToStringTransformer))



class BotLineProtocolTest(TestCase):


    def test_connectionMade(self):
        """
        When a connection is made, the protocol should set its eventReceived
        method to receive events from the avatar.
        """
        avatar = Avatar()
        avatar.setEventReceiver = create_autospec(avatar.setEventReceiver)

        proto = BotLineProtocol(avatar)
        proto.makeConnection(StringTransport())
        avatar.setEventReceiver.assert_called_once_with(proto.eventReceived)


    def test_eventReceived(self):
        """
        Events should be spit out a transformed string on a single line.
        """
        avatar = Avatar()

        proto = BotLineProtocol(avatar)
        proto.event_transformer = MagicMock()
        proto.event_transformer.transform.return_value = 'transformed'

        proto.makeConnection(StringTransport())
        proto.eventReceived(AttrSet('hey', 'ho', 3))

        proto.event_transformer.transform.assert_called_once_with(
            AttrSet('hey', 'ho', 3))
        self.assertEqual(proto.transport.value(), 'transformed\r\n')


    def test_connectionLost(self):
        """
        When the connection is lost, the avatar should quit.
        """
        avatar = MagicMock()
        proto = BotLineProtocol(avatar)
        proto.connectionLost('reason')
        avatar.quit.assert_called_once_with()


    def test_lineReceived(self):
        """
        Lines received are intrepretted as a space-separated argument list
        and executed as a command on the avatar.  The result is returned over
        the wire.
        """
        avatar = MagicMock()
        avatar.availableCommands = lambda: {'move': Move}
        avatar.execute.return_value = ('ret', 'val')
        
        proto = BotLineProtocol(avatar)
        proto.makeConnection(StringTransport())

        proto.lineReceived('move east-23 twice 3')
        avatar.execute.assert_called_once_with(Move, 'east-23', 'twice', 3)

        self.assertEqual(proto.transport.value(),
                    proto.event_transformer.transform(('ret', 'val'))+'\r\n',
                    "Should send the result over the wire.")


    def test_commandResultNull(self):
        """
        If the result of a command is None or '', don't send anything over
        the wire.
        """
        avatar = MagicMock()
        avatar.availableCommands = lambda: {'move': Move}
        avatar.execute.return_value = None
        
        proto = BotLineProtocol(avatar)
        proto.makeConnection(StringTransport())

        proto.lineReceived('move east-23 twice 3')

        self.assertEqual(proto.transport.value(), '')


    def test_commandResultDeferredSuccess(self):
        """
        If the result of a command is Deferred, wait for it to succeed.
        """
        avatar = MagicMock()
        avatar.availableCommands = lambda: {'move': Move}
        avatar.execute.return_value = defer.succeed('foo')
        
        proto = BotLineProtocol(avatar)
        proto.makeConnection(StringTransport())

        proto.lineReceived('move east-23 twice 3')

        self.assertEqual(proto.transport.value(), 'foo\r\n')


    def test_commandResultDeferredError(self):
        """
        If the result is a deferred failure, say something on the wire.
        """
        avatar = MagicMock()
        avatar.availableCommands = lambda: {'move': Move}
        avatar.execute.return_value = defer.fail(Exception('foo'))
        
        proto = BotLineProtocol(avatar)
        proto.makeConnection(StringTransport())

        proto.lineReceived('move east-23 twice 3')

        self.assertEqual(proto.transport.value(),
                         '%s\r\n' % (Exception('foo'),))











