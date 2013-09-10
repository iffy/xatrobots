
from zope.interface import implements

from xatro.interface import IXatroEngine
from xatro.error import NotAllowed
from xatro.router import Router
from xatro import action as act
from xatro.event import ActionPerformed, Destroyed, AttrSet

from collections import defaultdict
from functools import wraps



def requireSameSquare(*attrs):
    def deco(func):
        @wraps(func)
        def wrapper(instance, world, action):
            locations = set()
            for attr in attrs:
                obj = world.get(getattr(action, attr))
                locations.add(obj.get('location', None))
            if len(locations) != 1:
                raise NotAllowed("Must be in the same place")
            return func(instance, world, action)
        return wrapper
    return deco


def requireSquare(func):
    @wraps(func)
    def wrapper(instance, world, action):
        obj = world.get(action.subject())
        if obj.get('location') is None:
            raise NotAllowed("You must be on the board")
        return func(instance, world, action)
    return wrapper


def requireOnDeck(func):
    @wraps(func)
    def wrapper(instance, world, action):
        obj = world.get(action.subject())
        if obj.get('location') is not None:
            raise NotAllowed("You can only do this on deck")
        return func(instance, world, action)
    return wrapper


def requireTool(tool):
    def deco(func):
        @wraps(func)
        def wrapper(instance, world, action):
            obj = world.get(action.subject())
            if obj.get('tool') != tool:
                raise NotAllowed("You must have a %s equipped" % (tool,))
            return func(instance, world, action)
        return wrapper
    return deco


def requireVulnerable(target_attr):
    def deco(func):
        @wraps(func)
        def wrapper(instance, world, action):
            obj = world.get(getattr(action, target_attr))
            if not obj.get('hp'):
                raise NotAllowed("The target isn't a vulnerable thing")
            return func(instance, world, action)
        return wrapper
    return deco


def requireKind(attr_name, required_kind):
    def deco(func):
        @wraps(func)
        def wrapper(instance, world, action):
            obj = world.get(getattr(action, attr_name))
            if obj.get('kind') != required_kind:
                raise NotAllowed("You can't do that with a %s" % (
                                 obj.get('kind'),))
            return func(instance, world, action)
        return wrapper
    return deco    



class StandardRules(object):
    """
    I am the standard set of rules for a xatrobots game.
    """

    implements(IXatroEngine)

    energy_requirements = {
        act.MakeTool: 1,
        act.OpenPortal: 1,
        act.AddLock: 2,
        act.BreakLock: 2,
    }

    shoot_energy_requirements = {
        # hp, energy
        1: 1,
        2: 2,
        3: 2,
        4: 3,
        5: 3,
        6: 3,
    }

    repair_energy_requirements = shoot_energy_requirements.copy()

    ev_router = Router()
    act_router = Router()
    isAllowedRouter = Router()


    def __init__(self):
        self.bot_teams = {}
        self.bots_per_team_on_squares = defaultdict(lambda: set())


    def worldEventReceived(self, world, event):
        try:
            return self.ev_router.call(event.__class__, world, event)
        except KeyError:
            pass


    @ev_router.handle(ActionPerformed)
    def _whenActionPerformed(self, world, event):
        try:
            return self.act_router.call(event.action.__class__, world,
                                        event.action)
        except KeyError:
            pass

    @ev_router.handle(AttrSet)
    def _whenAttrSet(self, world, event):
        obj = world.get(event.id)
        if obj['kind'] == 'bot':
            if event.name == 'team':
                self.bot_teams[event.id] = event.value
            elif event.name == 'location':
                team = obj.get('team', None)
                if event.value is None:
                    # sending to the deck
                    self.bots_per_team_on_squares[team].remove(event.id)
                else:
                    # sending to a square
                    self.bots_per_team_on_squares[team].add(event.id)

    @ev_router.handle(Destroyed)
    def _whenDestroyed(self, world, event):
        if event.id in self.bot_teams:
            # indicate that this bot is no longer on the board
            team = self.bot_teams.pop(event.id)
            self.bots_per_team_on_squares[team].remove(event.id)


    def isAllowed(self, world, action):
        obj = world.get(action.subject())
        kind = obj.get('kind', None)
        if kind != 'bot':
            raise NotAllowed("Only bots can do that")

        try:
            return self.isAllowedRouter.call(action.__class__, world, action)
        except KeyError:
            pass


    
    @isAllowedRouter.handle(act.ConsumeEnergy)
    @isAllowedRouter.handle(act.OpenPortal)
    @isAllowedRouter.handle(act.AddLock)
    @isAllowedRouter.handle(act.BreakLock)
    @requireSquare
    def isAllowed_onSquare(self, world, action):
        pass


    @isAllowedRouter.handle(act.JoinTeam)
    @isAllowedRouter.handle(act.CreateTeam)
    @requireOnDeck
    def isAllowed_offSquare(self, world, action):
        pass


    @isAllowedRouter.handle(act.ShareEnergy)
    @requireSquare
    @requireKind('receiver', 'bot')
    @requireSameSquare('giver', 'receiver')
    def isAllowed_ShareEnergy(self, world, action):
        pass

    @isAllowedRouter.handle(act.Charge)
    @requireSquare
    def isAllowed_Charge(self, world, action):
        obj = world.get(action.thing)
        if obj.get('created_energy', 0):
            raise NotAllowed("You must wait until the last energy you created"
                             " is consumed or wasted")


    @isAllowedRouter.handle(act.Shoot)
    @requireSquare
    @requireSameSquare('shooter', 'target')
    @requireTool('cannon')
    @requireVulnerable('target')
    def isAllowed_Shoot(self, world, action):
        pass


    @isAllowedRouter.handle(act.Repair)
    @requireSquare
    @requireSameSquare('repairman', 'target')
    @requireTool('wrench')
    @requireVulnerable('target')
    def isAllowed_Repair(self, world, action):
        pass


    @isAllowedRouter.handle(act.MakeTool)
    @requireSquare
    @requireKind('ore', 'ore')
    @requireSameSquare('thing', 'ore')
    def isAllowed_MakeTool(self, world, action):
        pass


    @isAllowedRouter.handle(act.Move)
    def isAllowed_Move(self, world, action):
        obj = world.get(action.thing)

        if not obj.get('team'):
            raise NotAllowed("You must be part of a team before "
                             "landing")
        if self.bots_per_team_on_squares[obj.get('team', None)]:
            raise NotAllowed("Only the first bot can land without "
                             "a portal")


    @isAllowedRouter.handle(act.UsePortal)
    @requireOnDeck
    def isAllowed_UsePortal(self, world, action):
        obj = world.get(action.thing)

        if not obj.get('team'):
            raise NotAllowed("You must be part of a team before using a portal")



    def energyRequirement(self, world, action):
        """
        Get the integer amount of energy required to do an action.
        """
        if isinstance(action, act.Shoot):
            return self.shoot_energy_requirements[action.damage]
        elif isinstance(action, act.Repair):
            return self.repair_energy_requirements[action.amount]
        return self.energy_requirements.get(action.__class__, 0)


    def workRequirement(self, world, action):
        """
        """
        # XXX nothing requires work right now
        pass
