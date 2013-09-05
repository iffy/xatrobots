from twisted.application import service, internet
from twisted.internet import endpoints, protocol
from twisted.python import log
from twisted.python import usage


from xatro.world import World


class Options(usage.Options):
    """
    
    """
    
    optParameters = [
        ("line-proto-endpoint", "l", "tcp:7601",
         "string endpoint description to listen with line receiving protocol"),
    ]



class SetupService(service.Service):
    name = 'Setup Service'

    def __init__(self, reactor):
        self.reactor = reactor

    def startService(self):
        """
        Custom initialisation code goes here.
        """
        log.msg("Retriculating Splines")

        self.reactor.callLater(3, self.done)

    def done(self):
        log.msg("Finished retriculating splines")



def makeService(options):
    
    world = World()
    from twisted.internet import reactor

    f = ExampleFactory(debug=debug)
    endpoint = endpoints.serverFromString(reactor, options['endpoint'])
    server_service = internet.StreamServerEndpointService(endpoint, f)
    server_service.setName('Example Server')

    setup_service = SetupService(reactor)

    ms = service.MultiService()
    server_service.setServiceParent(ms)
    setup_service.setServiceParent(ms)

    return ms