from xatro.event import Created, Destroyed, AttrSet, ItemAdded, ItemRemoved
from xatro.event import ActionPerformed
from xatro.action import Move, Charge, ShareEnergy



class Mapper(object):


    def __init__(self, mapping=None, instance=None):
        self._mapping = mapping or {}
        self._instance = instance


    def __get__(self, instance, type=None):
        return Mapper(self._mapping, instance)


    def call(self, key, *args, **kwargs):
        func = self._mapping[key]
        return func(self._instance, *args, **kwargs)


    def handle(self, key):
        def deco(f):
            self._mapping[key] = f
            return f
        return deco



class ToStringTransformer(object):
    """
    I convert events to strings.
    """

    m = Mapper()

    def transform(self, what):
        """
        Transform the thing into a string, if possible.
        """
        try:
            return self.m.call(what.__class__, what)
        except KeyError:
            return str(what)


    @m.handle(Created)
    def Created(self, (id,)):
        return '%s CREATED' % (id,)


    @m.handle(Destroyed)
    def Destroyed(self, (id,)):
        return '%s DESTROYED' % (id,)


    @m.handle(AttrSet)
    def AttrSet(self, (id, name, val)):
        return '%s.%s = %r' % (id, name, val)


    @m.handle(ItemAdded)
    def ItemAdded(self, (id, name, val)):
        return '%s.%s ADD %r' % (id, name, val)


    @m.handle(ItemRemoved)
    def ItemRemoved(self, (id, name, val)):
        return '%s.%s POP %r' % (id, name, val)


    @m.handle(ActionPerformed)
    def ActionPerformed(self, (action,)):
        transformed_action = self.transform(action)
        return 'ACTION %s' % (transformed_action,)


    @m.handle(Move)
    def Move(self, action):
        return '%s moved to %s' % (action.thing, action.dst)


    @m.handle(Charge)
    def Charge(self, action):
        return '%s charged' % (action.thing,)


    @m.handle(ShareEnergy)
    def ShareEnergy(self, action):
        return '%s gave %s %d energy' % (action.giver, action.receiver, action.amount)



