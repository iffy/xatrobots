from twisted.trial.unittest import TestCase

from xatro.event import Created, Destroyed, AttrSet, ItemAdded, ItemRemoved
from xatro.event import ActionPerformed, AttrDel
from xatro.action import Move, Charge, ShareEnergy, ConsumeEnergy, Look, Shoot
from xatro.action import Repair, MakeTool, OpenPortal, UsePortal, ListSquares
from xatro.action import AddLock, BreakLock, JoinTeam
from xatro.transformer import ToStringTransformer, DictTransformer



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


    def test_AttrDel(self):
        self.assertSimple(AttrDel('bob', 'foo'), "bob.foo DEL")


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


    def test_ConsumeEnergy(self):
        self.assertSimple(ConsumeEnergy('foo', 10),
                          'foo consumed 10 energy')


    def test_Look(self):
        self.assertSimple(Look('foo'), 'foo looked around')


    def test_Shoot(self):
        self.assertSimple(Shoot('foo', 'bar', 3), 'foo shot bar for 3')


    def test_Repair(self):
        self.assertSimple(Repair('foo', 'bar', 9), 'foo repaired bar by 9')


    def test_MakeTool(self):
        self.assertSimple(MakeTool('foo', 'bar', 'knife'),
                          'foo made bar into knife')

    def test_OpenPortal(self):
        self.assertSimple(OpenPortal('foo', 'ore', 'joe'),
                          'foo used ore to open a portal for joe')

    def test_UsePortal(self):
        self.assertSimple(UsePortal('foo', '1234'), 'foo used portal 1234')


    def test_ListSquares(self):
        self.assertSimple(ListSquares('foo'), 'foo listed squares')


    def test_AddLock(self):
        self.assertSimple(AddLock('foo', 'bar'), 'foo added lock to bar')


    def test_BreakLock(self):
        self.assertSimple(BreakLock('foo', 'bar'), 'foo broke lock on bar')


    def test_JoinTeam(self):
        self.assertSimple(JoinTeam('foo', 'bar'), 'foo joined team bar')



class DictTransformerTest(TestCase):


    def assertSimple(self, ev, expected):
        """
        Assert that a basic, no-world-interaction event is transformed in
        the right way.
        """
        tx = DictTransformer()
        self.assertEqual(tx.transform(ev), expected)


    def test_unknown(self):
        """
        Unknown events are exceptions empty dicts
        """
        tx = DictTransformer()
        self.assertRaises(Exception, tx.transform, 'foo')


    def test_Created(self):
        self.assertSimple(Created('bob'), {'ev': 'created', 'id': 'bob'})


    def test_Destroyed(self):
        self.assertSimple(Destroyed('bob'), {'ev': 'destroyed', 'id': 'bob'})


    def test_AttrSet(self):
        self.assertSimple(AttrSet('bob', 'foo', 'val'), {
                            'ev': 'attrset',
                            'id': 'bob',
                            'name': 'foo',
                            'value': 'val'})


    def test_AttrDel(self):
        self.assertSimple(AttrDel('bob', 'foo'), {
                            'ev': 'attrdel',
                            'id': 'bob',
                            'name': 'foo'})


    def test_ItemAdded(self):
        self.assertSimple(ItemAdded('bob', 'foo', 'something'), {
                            'ev': 'itemadded',
                            'id': 'bob',
                            'name': 'foo',
                            'value': 'something'})


    def test_ItemRemoved(self):
        self.assertSimple(ItemRemoved('bob', 'foo', 'hey'), {
                            'ev': 'itemremoved',
                            'id': 'bob',
                            'name': 'foo',
                            'value': 'hey'})


    def test_ActionPerformed(self):
        self.assertSimple(ActionPerformed('foo'),
                            {'ev': 'action', 'action': 'foo'})


    def test_Move(self):
        self.assertSimple(Move('foo', 'dst'), {
                            'action': 'move',
                            'subject': 'foo',
                            'target': 'dst'})


    def test_Charge(self):
        self.assertSimple(Charge('foo'), {
                            'action': 'charge',
                            'subject': 'foo'})


    def test_ShareEnergy(self):
        self.assertSimple(ShareEnergy('foo', 'bar', 10), {
                            'action': 'share',
                            'subject': 'foo',
                            'target': 'bar',
                            'amount': 10})


    def test_ConsumeEnergy(self):
        self.assertSimple(ConsumeEnergy('foo', 10), {
                            'action': 'consume',
                            'subject': 'foo',
                            'amount': 10})


    def test_Look(self):
        self.assertSimple(Look('foo'), {
                            'action': 'look',
                            'subject': 'foo'})


    def test_Shoot(self):
        self.assertSimple(Shoot('foo', 'bar', 3), {
                            'action': 'shoot',
                            'subject': 'foo',
                            'target': 'bar',
                            'damage': 3})


    def test_Repair(self):
        self.assertSimple(Repair('foo', 'bar', 9), {
                            'action': 'repair',
                            'subject': 'foo',
                            'target': 'bar',
                            'amount': 9})


    def test_MakeTool(self):
        self.assertSimple(MakeTool('foo', 'bar', 'knife'), {
                            'action': 'maketool',
                            'subject': 'foo',
                            'ore': 'bar',
                            'tool': 'knife'})


    def test_OpenPortal(self):
        self.assertSimple(OpenPortal('foo', 'ore', 'joe'), {
                            'action': 'openportal',
                            'subject': 'foo',
                            'ore': 'ore',
                            'portal_user': 'joe'})


    def test_UsePortal(self):
        self.assertSimple(UsePortal('foo', '1234'), {
                            'action': 'useportal',
                            'subject': 'foo',
                            'portal': '1234'})


    def test_ListSquares(self):
        self.assertSimple(ListSquares('foo'), {
                            'action': 'listsquares',
                            'subject': 'foo'})


    def test_AddLock(self):
        self.assertSimple(AddLock('foo', 'bar'), {
                            'action': 'addlock',
                            'subject': 'foo',
                            'target': 'bar'})


    def test_BreakLock(self):
        self.assertSimple(BreakLock('foo', 'bar'), {
                            'action': 'breaklock',
                            'subject': 'foo',
                            'target': 'bar'})


    def test_JoinTeam(self):
        self.assertSimple(JoinTeam('foo', 'bar'), {
                            'action': 'jointeam',
                            'subject': 'foo',
                            'team': 'bar'})



