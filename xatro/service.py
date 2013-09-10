from twisted.application import service, internet
from twisted.internet import endpoints
from twisted.python import usage
from twisted.python.filepath import FilePath

from twisted.web.server import Site

from xatro.world import World
from xatro import action
from xatro.auth import FileStoredPasswords
from xatro.server.lineproto import BotFactory
from xatro.server import amp
from xatro.engine import XatroEngine
from xatro.web.observatory import GameObserver


class Options(usage.Options):
    """
    
    """
    
    optParameters = [
        ("line-proto-endpoint", "l", "tcp:7601",
         "string endpoint description to listen for line receiving protocol"),

        ("amp-proto-endpoint", "a", "tcp:7602",
         "string endpoing description to listen for AMP connections on"),

        ("web-endpoint", "w", "tcp:7600",
         "string endpoint web interface will listen on"),
        ("web-static-path", None, "static",
         "Path where static resources reside."),

        ('password-file', 'p', '.xatro.passwords',
         "File to store team passwords in"),
    ]



def makeBoard(world, options):
    """
    Make the board for the world.
    """
    from xatro.action import Move
    import random

    # XXX hard-coded 4 x 4 for now
    for i in xrange(4):
        for j in xrange(4):
            sq = world.create('square')['id']
            world.setAttr(sq, 'coordinates', (i, j))
            pylon = world.create('pylon')['id']
            world.setAttr(pylon, 'locks', 3)
            Move(pylon, sq).execute(world)
            for o in xrange(random.randint(1, 5)):
                ore = world.create('ore')['id']
                Move(ore, sq).execute(world)

            ls = world.create('lifesource')['id']
            Move(ls, sq).execute(world)



def makeService(options):
    from twisted.internet import reactor

    # rules/game engine
    from mock import MagicMock
    rules = MagicMock()
    rules.workRequirement.return_value = None
    rules.energyRequirement.return_value = 0
    rules.isAllowed.return_value = None

    engine = XatroEngine(rules)
    
    # web
    web_app = GameObserver(FilePath(options['web-static-path']))
    site = Site(web_app.app.resource())
    endpoint = endpoints.serverFromString(reactor, options['web-endpoint'])
    web_service = internet.StreamServerEndpointService(endpoint, site)
    web_service.setName('Web Observer Service')

    # passwords
    auth = FileStoredPasswords(options['password-file'])

    # world
    world = World(web_app.eventReceived, engine, auth)

    # make the board
    makeBoard(world, options)

    # AMP
    f = amp.AvatarFactory(world)
    endpoint = endpoints.serverFromString(reactor, options['amp-proto-endpoint'])
    amp_service = internet.StreamServerEndpointService(endpoint, f)
    amp_service.setName('AMP Bot Service')


    # line protocol
    f = BotFactory(world, {
        'move': action.Move,
        'charge': action.Charge,
        'consume': action.ConsumeEnergy,
        'share': action.ShareEnergy,
        'look': action.Look,
        'shoot': action.Shoot,
        'repair': action.Repair,
        'tool': action.MakeTool,
        'openportal': action.OpenPortal,
        'useportal': action.UsePortal,
        'squares': action.ListSquares,
        'createteam': action.CreateTeam,
        'jointeam': action.JoinTeam,
    })
    endpoint = endpoints.serverFromString(reactor, options['line-proto-endpoint'])
    line_service = internet.StreamServerEndpointService(endpoint, f)
    line_service.setName('Line-protocol Bot Service')

    ms = service.MultiService()
    line_service.setServiceParent(ms)
    web_service.setServiceParent(ms)
    amp_service.setServiceParent(ms)

    return ms


