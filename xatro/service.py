from twisted.application import service, internet
from twisted.internet import endpoints
from twisted.python import usage


from xatro.world import World
from xatro import action
from xatro.server.lineproto import BotFactory
from xatro.engine import XatroEngine


class Options(usage.Options):
    """
    
    """
    
    optParameters = [
        ("line-proto-endpoint", "l", "tcp:7601",
         "string endpoint description to listen for line receiving protocol"),
    ]



def makeService(options):
    from twisted.internet import reactor

    from mock import MagicMock
    rules = MagicMock()
    rules.workRequirement.return_value = None
    rules.energyRequirement.return_value = 0
    rules.isAllowed.return_value = None

    engine = XatroEngine(rules)
    world = World(lambda x:None, engine)
    
    f = BotFactory(world, {
        'move': action.Move,
        'charge': action.Charge,
        'consume': action.ConsumeEnergy,
        'share': action.ShareEnergy,
        'look': action.Look,
        'shoot': action.Shoot,
        'repair': action.Repair,
    })
    endpoint = endpoints.serverFromString(reactor, options['line-proto-endpoint'])
    server_service = internet.StreamServerEndpointService(endpoint, f)
    server_service.setName('Line-protocol Bot Service')

    ms = service.MultiService()
    server_service.setServiceParent(ms)

    return ms