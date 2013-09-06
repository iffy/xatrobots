from xatro.event import Created, Destroyed, AttrSet, ItemAdded, ItemRemoved
from xatro.event import ActionPerformed, AttrDel
from xatro import action
from xatro.router import Router



class ToStringTransformer(object):
    """
    I convert events to strings.
    """

    router = Router()

    def transform(self, what):
        """
        Transform the thing into a string, if possible.
        """
        try:
            return self.router.call(what.__class__, what)
        except KeyError:
            return str(what)


    @router.handle(Created)
    def Created(self, (id,)):
        return '%s CREATED' % (id,)


    @router.handle(Destroyed)
    def Destroyed(self, (id,)):
        return '%s DESTROYED' % (id,)


    @router.handle(AttrSet)
    def AttrSet(self, (id, name, val)):
        return '%s.%s = %r' % (id, name, val)


    @router.handle(AttrDel)
    def AttrDel(self, (id, name)):
        return '%s.%s DEL' % (id, name)
        

    @router.handle(ItemAdded)
    def ItemAdded(self, (id, name, val)):
        return '%s.%s ADD %r' % (id, name, val)


    @router.handle(ItemRemoved)
    def ItemRemoved(self, (id, name, val)):
        return '%s.%s POP %r' % (id, name, val)


    @router.handle(ActionPerformed)
    def ActionPerformed(self, (action,)):
        transformed_action = self.transform(action)
        return 'ACTION %s' % (transformed_action,)


    @router.handle(action.Move)
    def Move(self, action):
        return '%s moved to %s' % (action.thing, action.dst)


    @router.handle(action.Charge)
    def Charge(self, action):
        return '%s charged' % (action.thing,)


    @router.handle(action.ShareEnergy)
    def ShareEnergy(self, action):
        return '%s gave %s %d energy' % (action.giver, action.receiver, action.amount)


    @router.handle(action.ConsumeEnergy)
    def ConsumeEnergy(self, action):
        return '%s consumed %d energy' % (action.thing, action.amount)


    @router.handle(action.Shoot)
    def Shoot(self, action):
        return '%s shot %s for %d' % (action.shooter, action.target,
                                      action.damage)

    @router.handle(action.Repair)
    def Repair(self, action):
        return '%s repaired %s by %d' % (action.repairman, action.target,
                                         action.amount)

    @router.handle(action.Look)
    def Look(self, action):
        return '%s looked around' % (action.thing,)


    @router.handle(action.MakeTool)
    def MakeTool(self, action):
        return '%s made %s into %s' % (action.thing, action.ore, action.tool)


    @router.handle(action.OpenPortal)
    def OpenPortal(self, action):
        return '%s used %s to open a portal for %s' % (action.thing,
                                                       action.ore,
                                                       action.user)

    @router.handle(action.UsePortal)
    def UsePortal(self, action):
        return '%s used portal %s' % (action.thing, action.portal)


    @router.handle(action.ListSquares)
    def ListSquares(self, action):
        return '%s listed squares' % (action.eyes,)


    @router.handle(action.AddLock)
    def AddLock(self, action):
        return '%s added lock to %s' % (action.doer, action.target)


    @router.handle(action.BreakLock)
    def BreakLock(self, action):
        return '%s broke lock on %s' % (action.doer, action.target)


    @router.handle(action.JoinTeam)
    def JoinTeam(self, action):
        return '%s joined team %s' % (action.thing, action.team_name)




