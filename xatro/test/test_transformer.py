from twisted.trial.unittest import TestCase

from xatro.event import Created, Destroyed, AttrSet, ItemAdded, ItemRemoved
from xatro.event import ActionPerformed
from xatro.action import Move, Charge, ShareEnergy
from xatro.transformer import ToStringTransformer



class ToStringTransformerTest(TestCase):


    def assertSimple(self, ev, expected):
        """
        Assert that a basic, no-world-interaction event is transformed in
        the right way.
        """
        tx = ToStringTransformer()
        self.assertEqual(tx.transform(ev), expected)


    def test_unknown(self):
        """
        Unknown events are just coerced to a string.
        """
        self.assertSimple('foo', str('foo'))


    def test_Created(self):
        self.assertSimple(Created('bob'), 'bob CREATED')


    def test_Destroyed(self):
        self.assertSimple(Destroyed('bob'), 'bob DESTROYED')


    def test_AttrSet(self):
        self.assertSimple(AttrSet('bob', 'foo', 'val'),
                          "bob.foo = %r" % ('val',))

    def test_ItemAdded(self):
        self.assertSimple(ItemAdded('bob', 'foo', 'something'),
                          "bob.foo ADD %r" % ('something',))


    def test_ItemRemoved(self):
        self.assertSimple(ItemRemoved('bob', 'foo', 'hey'),
                          "bob.foo POP %r" % ('hey',))


    def test_ActionPerformed(self):
        self.assertSimple(ActionPerformed('foo'), 'ACTION foo')


    def test_Move(self):
        self.assertSimple(Move('foo', 'dst'),
                          'foo moved to dst')


    def test_Charge(self):
        self.assertSimple(Charge('foo'), 'foo charged')


    def test_ShareEnergy(self):
        self.assertSimple(ShareEnergy('foo', 'bar', 10),
                          'foo gave bar 10 energy')