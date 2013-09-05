from twisted.application import service, internet
from twisted.internet import endpoints
from twisted.python import usage


from xatro.world import World
from xatro import action
from xatro.server.lineproto import BotFactory


class Options(usage.Options):
    """
    
    """
    
    optParameters = [
        ("line-proto-endpoint", "l", "tcp:7601",
         "string endpoint description to listen for line receiving protocol"),
    ]



def makeService(options):
    from twisted.internet import reactor

    world = World(lambda x:None)
    
    f = BotFactory(world, {
        'move': action.Move,
    })
    endpoint = endpoints.serverFromString(reactor, options['line-proto-endpoint'])
    server_service = internet.StreamServerEndpointService(endpoint, f)
    server_service.setName('Line-protocol Bot Service')

    ms = service.MultiService()
    server_service.setServiceParent(ms)

    return ms