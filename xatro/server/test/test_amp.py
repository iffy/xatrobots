from twisted.trial.unittest import TestCase
from twisted.internet import defer

from mock import create_autospec, MagicMock

import json

from xatro.transformer import DictTransformer
from xatro.event import AttrSet
from xatro.world import World
from xatro.avatar import Avatar
from xatro.server.amp import AvatarProtocol, AvatarFactory, Identify
from xatro.server.amp import ReceiveEvent



class AvatarFactoryTest(TestCase):


    def test_world(self):
        """
        The factory should know about the world.
        """
        f = AvatarFactory('world')
        self.assertEqual(f.world, 'world')


    def test_buildProtocol(self):
        """
        Should pass on the world to the protocol.
        """
        f = AvatarFactory('world')
        p = f.buildProtocol(None)
        self.assertEqual(p.factory, f)
        self.assertEqual(p.world, 'world')
        self.assertTrue(isinstance(p, AvatarProtocol))




class AvatarProtocolTest(TestCase):


    def test_connectionMade(self):
        """
        When the connection is made, a bot should be created and the id of the
        created bot should be sent over the wire.
        """
        world = World(MagicMock())
        p = AvatarProtocol(world)
        p.callRemote = create_autospec(p.callRemote)

        p.connectionMade()
        self.assertTrue(isinstance(p.avatar, Avatar))
        self.assertEqual(p.avatar._world, world, "Should set the world on "
                         "the avatar")

        p.callRemote.assert_called_once_with(Identify, id=p.avatar._game_piece)

        # check that event receiving is set up
        p.callRemote.reset_mock()
        p.avatar.eventReceived(AttrSet('id', 'name', 'val'))
        transformer = DictTransformer()
        expected = json.dumps(transformer.transform(AttrSet('id', 'name', 'val')))
        p.callRemote.assert_called_once_with(ReceiveEvent, ev=expected)


    @defer.inlineCallbacks
    def test_handleWorldCommand(self):
        """
        World commands without work should call execute on the avatar.
        """
        world = World(MagicMock())
        p = AvatarProtocol(world)
        p.avatar = MagicMock()
        p.avatar.execute.return_value = {"hey": "ho"}

        FooCls = MagicMock()
        p.commands = {
            'foo': FooCls,
        }

        r = yield p.handleWorldCommand(name='foo', args=['foo', 'bar', 'baz'],
                                       work=None)
        p.avatar.execute.assert_called_once_with(FooCls, 'foo', 'bar', 'baz')
        self.assertEqual(r, {'data': json.dumps({"hey":"ho"})})



