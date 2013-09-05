from xatro.event import Created, Destroyed, AttrSet, ItemAdded, ItemRemoved
from xatro.event import ActionPerformed
from xatro.action import Move, Charge, ShareEnergy
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


    @router.handle(Move)
    def Move(self, action):
        return '%s moved to %s' % (action.thing, action.dst)


    @router.handle(Charge)
    def Charge(self, action):
        return '%s charged' % (action.thing,)


    @router.handle(ShareEnergy)
    def ShareEnergy(self, action):
        return '%s gave %s %d energy' % (action.giver, action.receiver, action.amount)



