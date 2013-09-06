from twisted.application import service, internet
from twisted.internet import endpoints
from twisted.python import usage
from twisted.python.filepath import FilePath

from twisted.web.server import Site

from xatro.world import World
from xatro import action
from xatro.server.lineproto import BotFactory
from xatro.engine import XatroEngine
from xatro.web.observatory import GameObserver


class Options(usage.Options):
    """
    
    """
    
    optParameters = [
        ("line-proto-endpoint", "l", "tcp:7601",
         "string endpoint description to listen for line receiving protocol"),
        ("web-endpoint", "w", "tcp:7600",
         "string endpoint web interface will listen on"),
        ("web-static-path", None, "static",
         "Path where static resources reside.")
    ]



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

    # world
    world = World(web_app.eventReceived, engine)

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
    })
    endpoint = endpoints.serverFromString(reactor, options['line-proto-endpoint'])
    line_service = internet.StreamServerEndpointService(endpoint, f)
    line_service.setName('Line-protocol Bot Service')

    ms = service.MultiService()
    line_service.setServiceParent(ms)
    web_service.setServiceParent(ms)

    return ms