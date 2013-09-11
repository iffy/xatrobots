from twisted.internet import protocol, defer
from twisted.protocols import amp

import json

from xatro.transformer import DictTransformer
from xatro.avatar import Avatar
from xatro import action
from xatro.error import NotAllowed, NotEnoughEnergy



class Identify(amp.Command):
    
    arguments = [
        ('id', amp.String()),
    ]
    requiresAnswer = False



class ReceiveEvent(amp.Command):
    
    arguments = [
        ('ev', amp.String()),
    ]
    requiresAnswer = False


class WorldCommand(amp.Command):

    arguments = [
        ('name', amp.String()),
        ('args', amp.ListOf(amp.String())),
        ('work', amp.String(optional=True)),
    ]
    response = [
        ('data', amp.String()),
    ]
    errors = {
        NotAllowed: 'NOT_ALLOWED',
        NotEnoughEnergy: 'NOT_ENOUGH_ENERGY',
        KeyError: 'NOT_FOUND',
    }




class AvatarProtocol(amp.AMP):


    def __init__(self, world):
        amp.AMP.__init__(self)
        self.world = world
        self.transformer = DictTransformer()

        # XXX I feel like this is what AMP was made for :(
        self.commands = {
            'move': action.Move,
            'look': action.Look,
            'lookat': action.LookAt,
            'charge': action.Charge,
            'share': action.ShareEnergy,
            'shoot': action.Shoot,
            'repair': action.Repair,
            'maketool': action.MakeTool,
            'openportal': action.OpenPortal,
            'useportal': action.UsePortal,
            'listsquares': action.ListSquares,
            'addlock': action.AddLock,
            'breaklock': action.BreakLock,
            'createteam': action.CreateTeam,
            'jointeam': action.JoinTeam,
        }
    

    def connectionMade(self):
        self.avatar = Avatar(self.world)
        
        # hook up events
        self.avatar.setEventReceiver(self.eventReceived)
        # create bot
        
        bot = self.world.create('bot')['id']
        self.avatar.setGamePiece(bot)

        # notify the other side
        self.callRemote(Identify, id=bot)


    def eventReceived(self, event):
        self.callRemote(ReceiveEvent,
                        ev=json.dumps(self.transformer.transform(event)))
        # XXX sending json over AMP feels wrong :(


    @WorldCommand.responder
    def handleWorldCommand(self, name, args, work=None):
        print name, args
        cls = self.commands[name]
        if name in ['share', 'shoot', 'repair']:
            args = (args[0], int(args[1]))
        d = defer.maybeDeferred(self.avatar.execute, cls, *args)
        d.addCallback(lambda r: {'data': json.dumps(r)})
        return d


    def connectionLost(self, reason):
        self.avatar.quit()



class AvatarFactory(protocol.Factory):
    
    protocol = AvatarProtocol

    def __init__(self, world):
        self.world = world


    def buildProtocol(self, addr):
        p = self.protocol(self.world)
        p.factory = self
        return p