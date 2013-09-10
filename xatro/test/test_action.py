from twisted.trial.unittest import TestCase
from twisted.internet import defer
from zope.interface.verify import verifyObject

from mock import MagicMock

from xatro.interface import IAction
from xatro.world import World
from xatro.action import Move, Charge, ShareEnergy, ConsumeEnergy, Shoot
from xatro.action import Repair, Look, MakeTool, OpenPortal, UsePortal
from xatro.action import ListSquares, AddLock, BreakLock, JoinTeam
from xatro.action import CreateTeam
from xatro.event import Destroyed
from xatro.auth import FileStoredPasswords
from xatro.error import NotEnoughEnergy, Invulnerable, NotAllowed, BadPassword



class MoveTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, Move('foo', 'bar'))


    def test_emitters(self):
        self.assertEqual(Move('foo', 'bar').emitters(), ['foo'])


    def test_subject(self):
        self.assertEqual(Move('foo', 'bar').subject(), 'foo')


    def test_execute(self):
        """
        Moving to a new location should:

            - Cause C{location} to be updated
            - Cause C{contents} to be updated
            - Subscribe the thing to the location's events
            - Subscribe the location to the thing's events
        """
        world = World(MagicMock())
        thing = world.create('thing')
        room = world.create('room')

        move = Move(thing['id'], room['id'])
        move.execute(world)

        self.assertEqual(thing['location'], room['id'], "Should set location")
        self.assertEqual(room['contents'], [thing['id']], "Should set contents")

        room_called = []
        world.receiveFor(room['id'], room_called.append)

        thing_called = []
        world.receiveFor(thing['id'], thing_called.append)

        world.emit('foo', room['id'])
        self.assertEqual(room_called, ['foo'],
                         "Room should receive room events")
        self.assertEqual(thing_called, ['foo'],
                         "Thing should receive room events")

        room_called.pop()
        thing_called.pop()

        world.emit('foo', thing['id'])
        self.assertEqual(room_called, ['foo'],
                         "Room should receive thing events")
        self.assertEqual(thing_called, ['foo'],
                         "Thing should receive thing events")


    def test_execute_inRoom(self):
        """
        If an object is already located in another container, then moving it
        should:
            - Unsubscribe from the location's events
            - Unsubscribe the location from the thing's events
            - Cause C{contents} to be updated.
        """
        world = World(MagicMock())
        thing = world.create('thing')['id']
        room1 = world.create('room1')['id']
        room2 = world.create('room2')['id']

        move1 = Move(thing, room1)
        move1.execute(world)

        move2 = Move(thing, room2)
        move2.execute(world)

        room1_called = []
        world.receiveFor(room1, room1_called.append)

        room2_called = []
        world.receiveFor(room2, room2_called.append)

        thing_called = []
        world.receiveFor(thing, thing_called.append)

        # emit from room1
        world.emit('foo', room1)
        self.assertEqual(thing_called, [], "Thing should detach from previous "
                         "room events")
        room1_called.pop()

        # emit from thing
        world.emit('bar', thing)
        self.assertEqual(thing_called, ['bar'], "Thing should see own events")
        self.assertEqual(room1_called, [], "Room1 should detach from thing"
                         " events")

        # room1 contents
        room1_obj = world.get(room1)
        self.assertEqual(room1_obj['contents'], [], "Should remove from "
                         "contents of room1")

        location = world.get(thing)['location']
        self.assertEqual(location, room2, "Should update the "
                         "location of the thing.  This is mostly to confirm "
                         "that the default moving behavior tested in the other "
                         "test happened.")


    def test_moveToNone(self):
        """
        Moving something to nowhere should result in the location being
        None.
        """
        world = World(MagicMock())
        thing = world.create('thing')['id']
        room1 = world.create('room1')['id']

        move1 = Move(thing, room1)
        move1.execute(world)

        move2 = Move(thing, None)
        move2.execute(world)

        room1_called = []
        world.receiveFor(room1, room1_called.append)

        thing_called = []
        world.receiveFor(thing, thing_called.append)

        # emit from room1
        world.emit('foo', room1)
        self.assertEqual(thing_called, [], "Thing should detach from previous "
                         "room events")
        room1_called.pop()

        # emit from thing
        world.emit('bar', thing)
        self.assertEqual(thing_called, ['bar'], "Thing should see own events")
        self.assertEqual(room1_called, [], "Room1 should detach from thing"
                         " events")

        # room1 contents
        room1_obj = world.get(room1)
        self.assertEqual(room1_obj['contents'], [], "Should remove from "
                         "contents of room1")

        location = world.get(thing)['location']
        self.assertEqual(location, None, "Should update the location")


    def test_invalidLocation(self):
        """
        It is an error to move to a non-entity.
        """
        world = World(MagicMock())
        thing = world.create('thing')['id']

        self.assertRaises(NotAllowed, Move(thing, 4).execute, world)


    def test_thingsInTheSameRoom(self):
        """
        Things in the same location should see events emitted by each other.
        """
        world = World(MagicMock())
        room = world.create('a')['id']
        thing1 = world.create('thing')['id']
        thing2 = world.create('thing')['id']

        Move(thing1, room).execute(world)
        Move(thing2, room).execute(world)

        c1 = []
        world.receiveFor(thing1, c1.append)
        c2 = []
        world.receiveFor(thing2, c2.append)

        world.emit('foo', thing1)
        self.assertEqual(c1, ['foo'])
        self.assertEqual(c2, ['foo'])



class ChargeTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, Charge('foo'))


    def test_emitters(self):
        self.assertEqual(Charge('foo').emitters(), ['foo'])


    def test_subject(self):
        self.assertEqual(Charge('foo').subject(), 'foo')


    def test_charge(self):
        """
        Charging should add energy to the thing's energy pool and to the
        thing's created energy pool.
        """
        world = World(MagicMock())

        thing = world.create('thing')

        charge = Charge(thing['id'])
        charge.execute(world)

        self.assertEqual(len(thing['energy']), 1)
        self.assertEqual(thing['created_energy'], 1, "Should keep track "
                         "of the energy it created")

        e = world.get(thing['energy'][0])
        self.assertEqual(e['kind'], 'energy')


    def test_energyDestroyed(self):
        """
        When energy is destroyed, it should decrement the creator's
        created_energy amount.
        """
        world = World(MagicMock())
        thing = world.create('thing')

        Charge(thing['id']).execute(world)

        energy = thing['energy'][0]
        world.destroy(energy)

        self.assertEqual(thing['energy'], [], "Should remove the energy from "
                         "the energy list of the user")
        self.assertEqual(thing['created_energy'], 0, "Should decrement "
                         "the created_energy attribute")


    def test_creator_dead(self):
        """
        When the creator of energy is dead, the energy is also dead.

        XXX I'm not sure if this belongs in the game engine or not.  Seems like
        a rule that could be changed.
        """
        world = World(MagicMock())
        thing = world.create('thing')

        Charge(thing['id']).execute(world)

        energy = thing['energy'][0]
        d = world.onEvent(energy, Destroyed(energy))

        # to die means to move to None
        Move(thing['id'], None).execute(world)

        self.assertEqual(d.called, True, "Energy should be destroyed because "
                         "the creator of the energy died.")



class ShareEnergyTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, ShareEnergy('foo', 'bar', 2))


    def test_emitters(self):
        self.assertEqual(ShareEnergy('foo', 'bar', 2).emitters(),
                         ['foo', 'bar'])


    def test_subject(self):
        self.assertEqual(ShareEnergy('foo', 'bar', 2).subject(), 'foo')


    def test_share(self):
        """
        Sharing energy should result in the energy being removed from the
        giver's energy pool and added to the receiver's energy pool.
        """
        world = World(MagicMock())
        giver = world.create('thing')
        receiver = world.create('thing')

        Charge(giver['id']).execute(world)
        ShareEnergy(giver['id'], receiver['id'], 1).execute(world)

        self.assertEqual(len(giver['energy']), 0,
                         "Should deplete giver's energy")
        self.assertEqual(len(receiver['energy']), 1,
                         "Should increase receiver's energy")


    def test_sharedEnergy_destroyed(self):
        """
        When shared energy is destroyed, it should be removed from the
        energy pool of whoever has it and still decrement the creator's
        created_energy amount.
        """
        world = World(MagicMock())
        giver = world.create('thing')
        receiver = world.create('thing')

        Charge(giver['id']).execute(world)
        ShareEnergy(giver['id'], receiver['id'], 1).execute(world)

        e = receiver['energy'][0]
        world.destroy(e)

        self.assertEqual(giver['created_energy'], 0,
                         "Should decrement creator's created count")
        self.assertEqual(len(receiver['energy']), 0,
                         "Should deplete receiver's energy")



class ConsumeEnergyTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, ConsumeEnergy('foo', 2))


    def test_emitters(self):
        self.assertEqual(ConsumeEnergy('foo', 2).emitters(), ['foo'])


    def test_subject(self):
        self.assertEqual(ConsumeEnergy('foo', 2).subject(), 'foo')


    def test_execute(self):
        """
        Consuming energy should simply destroy the energy.
        """
        world = World(MagicMock())
        thing = world.create('foo')

        Charge(thing['id']).execute(world)
        Charge(thing['id']).execute(world)

        energies = list(thing['energy'])

        ConsumeEnergy(thing['id'], 2).execute(world)

        self.assertNotIn(energies[0], world.objects)
        self.assertNotIn(energies[1], world.objects)


    def test_notEnough(self):
        """
        It is an error to consume more energy than you have.
        """
        world = World(MagicMock())
        thing = world.create('foo')

        Charge(thing['id']).execute(world)

        energies = list(thing['energy'])

        self.assertRaises(NotEnoughEnergy,
                          ConsumeEnergy(thing['id'], 2).execute, world)

        self.assertIn(energies[0], world.objects, "Should not have consumed "
                      "the energy")



class ShootTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, Shoot('foo', 'bar', 3))


    def test_emitters(self):
        self.assertEqual(Shoot('foo', 'bar', 3).emitters(), ['foo', 'bar'])


    def test_subject(self):
        self.assertEqual(Shoot('foo', 'bar', 3).subject(), 'foo')


    def test_execute(self):
        """
        Shooting something should reduce its hitpoints by the given amount.
        """
        world = World(MagicMock())
        thing = world.create('foo')
        target = world.create('foo')

        world.setAttr(target['id'], 'hp', 30)
        Shoot(thing['id'], target['id'], 10).execute(world)

        self.assertEqual(target['hp'], 20, "Should reduce the hitpoints")


    def test_stayAbove0(self):
        """
        You can't damage something below 0 by shooting.
        """
        world = World(MagicMock())
        thing = world.create('foo')
        target = world.create('foo')

        world.setAttr(target['id'], 'hp', 30)
        Shoot(thing['id'], target['id'], 500).execute(world)

        self.assertEqual(target['hp'], 0, "Should reduce the hitpoints to 0")


    def test_invulnerable(self):
        """
        You can't shoot something that is invulnerable.
        """
        world = World(MagicMock())
        thing = world.create('foo')
        target = world.create('foo')

        self.assertRaises(Invulnerable,
                          Shoot(thing['id'], target['id'], 500).execute, world)
        world.setAttr(target['id'], 'hp', None)
        self.assertRaises(Invulnerable,
                          Shoot(thing['id'], target['id'], 500).execute, world)



class RepairTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, Repair('foo', 'bar', 3))


    def test_emitters(self):
        self.assertEqual(Repair('foo', 'bar', '3').emitters(), ['foo', 'bar'])


    def test_subject(self):
        self.assertEqual(Repair('foo', 'bar', 3).subject(), 'foo')


    def test_execute(self):
        """
        Repairing something should increas the number of hitpoints on that
        thing.
        """
        world = World(MagicMock())
        thing = world.create('foo')
        target = world.create('foo')

        world.setAttr(target['id'], 'hp', 30)
        Repair(thing['id'], target['id'], 10).execute(world)

        self.assertEqual(target['hp'], 40, "Should increase the hitpoints")


    def test_invulnerable(self):
        """
        You can't repair something that is invulnerable.
        """
        world = World(MagicMock())
        thing = world.create('foo')
        target = world.create('foo')

        self.assertRaises(Invulnerable,
                          Repair(thing['id'], target['id'], 500).execute, world)
        world.setAttr(target['id'], 'hp', None)
        self.assertRaises(Invulnerable,
                          Repair(thing['id'], target['id'], 500).execute, world)



class LookTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, Look('foo'))


    def test_emitters(self):
        self.assertEqual(Look('foo').emitters(), ['foo'])


    def test_subject(self):
        self.assertEqual(Look('foo').subject(), 'foo')


    def test_inLocation(self):
        """
        Should list the things in my location
        """
        world = World(MagicMock())
        room = world.create('foo')
        thing = world.create('thing')
        other = world.create('thing')

        Move(thing['id'], room['id']).execute(world)
        Move(other['id'], room['id']).execute(world)

        r = Look(thing['id']).execute(world)
        self.assertEqual(set(r), set([thing['id'], other['id']]))


    def test_nowhere(self):
        """
        If you are nowhere, return an empty list.
        """
        world = World(MagicMock())
        thing = world.create('thing')

        self.assertEqual(Look(thing['id']).execute(world), [])



class MakeToolTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, MakeTool('me', 'ore', 'tool'))


    def test_emitters(self):
        self.assertEqual(MakeTool('me', 'ore', 'tool').emitters(),
                         ['me', 'ore'])


    def test_subject(self):
        self.assertEqual(MakeTool('foo', 'ore', 'tool').subject(), 'foo')


    def test_makeTool(self):
        """
        Making a tool will destroy the ore, make a lifesource in its place,
        and equip the maker with the tool.
        """
        world = World(MagicMock())
        ore = world.create('ore')
        bot = world.create('bot')
        MakeTool(bot['id'], ore['id'], 'knife').execute(world)

        self.assertEqual(ore['kind'], 'lifesource', "Should have converted "
                         "the ore into a lifesource")
        self.assertEqual(bot['tool'], 'knife', "Should have given the bot "
                         "the tool")


    def test_onlyOre(self):
        """
        Only ore can be turned into tools.
        """
        world = World(MagicMock())
        ore = world.create('flower')
        bot = world.create('bot')

        self.assertRaises(NotAllowed,
            MakeTool(bot['id'], ore['id'], 'knife').execute, world)


    def test_revertToOreWhenBotDies(self):
        """
        If the thing dies that made the tool, revert to ore and set the tool
        to None
        """
        world = World(MagicMock())
        ore = world.create('ore')
        bot = world.create('bot')
        MakeTool(bot['id'], ore['id'], 'knife').execute(world)

        # moving to None is death
        Move(bot['id'], None).execute(world)

        self.assertNotIn('tool', bot, "Should unequip the tool")
        self.assertEqual(ore['kind'], 'ore', "Should revert to ore")


    def test_revertWhenKilled(self):
        """
        If the lifesource is shot to death, then revert to ore and unequip.
        """
        world = World(MagicMock())
        ore = world.create('ore')
        bot = world.create('bot')
        MakeTool(bot['id'], ore['id'], 'knife').execute(world)

        world.setAttr(ore['id'], 'hp', 0)

        self.assertNotIn('tool', bot, "Should unequip the tool")
        self.assertEqual(ore['kind'], 'ore', "Should revert to ore")


    def test_makeSecondTool(self):
        """
        If you make a tool from a different piece of ore, your existing tool
        is unequipped and the lifesource it was made from is reverted to ore.
        """
        world = World(MagicMock())
        ore1 = world.create('ore')
        ore2 = world.create('ore')

        bot = world.create('bot')
        MakeTool(bot['id'], ore1['id'], 'knife').execute(world)

        MakeTool(bot['id'], ore2['id'], 'butterfly net').execute(world)

        self.assertEqual(bot['tool'], 'butterfly net',
                         "Should equip the new tool")
        self.assertEqual(ore1['kind'], 'ore', "Should revert to ore")
        self.assertEqual(ore2['kind'], 'lifesource')

        # kill original
        world.setAttr(ore1['id'], 'hp', 0)

        self.assertEqual(bot['tool'], 'butterfly net', "should not change tool"
                         " when the original ore dies")
        self.assertEqual(ore2['kind'], 'lifesource')



class OpenPortalTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, OpenPortal('me', 'ore', 'user'))


    def test_emitters(self):
        self.assertEqual(OpenPortal('me', 'ore', 'user').emitters(),
                         ['me', 'user'])


    def test_subject(self):
        self.assertEqual(OpenPortal('foo', 'bar', 'baz').subject(), 'foo')


    def test_open(self):
        """
        You can open a portal on from some ore.
        """
        world = World(MagicMock())
        ore = world.create('ore')
        bot = world.create('bot')
        OpenPortal(bot['id'], ore['id'], 'user').execute(world)

        self.assertEqual(ore['portal_user'], 'user', "Should set the portal "
                         "user to the id of the user that can use the portal")
        self.assertEqual(ore['kind'], 'portal')


    def test_openerDies(self):
        """
        If the opener dies before the portal is used, the portal reverts to
        ore.
        """
        world = World(MagicMock())
        ore = world.create('ore')
        bot = world.create('bot')
        OpenPortal(bot['id'], ore['id'], 'user').execute(world)

        # it is death to move to the void
        Move(bot['id'], None).execute(world)

        self.assertEqual(ore['kind'], 'ore')
        self.assertNotIn('portal_user', ore)



class UsePortalTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, UsePortal('me', 'portal_id'))


    def test_emitters(self):
        self.assertEqual(UsePortal('me', 'portal_id').emitters(), ['me'])


    def test_subject(self):
        self.assertEqual(UsePortal('foo', 'bar').subject(), 'foo')


    def usedPortal(self):
        self.world = World(MagicMock())
        self.place = self.world.create('place')
        self.ore = self.world.create('ore')
        self.bot = self.world.create('bot')
        self.lander = self.world.create('lander')
        
        Move(self.ore['id'], self.place['id']).execute(self.world)
        OpenPortal(self.bot['id'], self.ore['id'],
                   self.lander['id']).execute(self.world)
        UsePortal(self.lander['id'], self.ore['id']).execute(self.world)


    def test_use(self):
        """
        Using a portal will cause the thing that used it to be moved to the
        location where the portal is, remove the portal_user attribute from
        the portal.
        """
        self.usedPortal()
        lander = self.lander
        ore = self.ore

        self.assertEqual(lander['location'], ore['location'], "Should move "
                         "the lander into the location")


    def test_portalDestroyed(self):
        """
        If a portal is destroyed, the user of the portal is sent to the void.
        """
        self.usedPortal()

        # destroy the portal
        self.world.destroy(self.ore['id'])

        self.assertEqual(self.lander['location'], None, "Should send lander "
                         "to the void")


    def test_portalKilled(self):
        """
        If a portal is killed (by hp reaching 0) the user of the portal is sent
        to the void and the portal reverts to ore.
        """
        self.usedPortal()

        # kill the portal
        self.world.setAttr(self.ore['id'], 'hp', 0)

        self.assertEqual(self.lander['location'], None, "Should send lander "
                         "to the void")
        self.assertEqual(self.ore['kind'], 'ore', "Should revert to ore")
        self.assertNotIn('portal_user', self.ore, "Should delete portal_user "
                         "attribute")


    def test_portal_user_noMatch(self):
        """
        It is NotAllowed to use a portal with a portal_user different than the
        thing trying to use the portal.
        """
        world = World(MagicMock())
        place = world.create('place')
        ore = world.create('ore')
        bot = world.create('bot')
        lander = world.create('lander')
        imposter = world.create('imposter')
        
        Move(ore['id'], place['id']).execute(world)
        OpenPortal(bot['id'], ore['id'],
                   lander['id']).execute(world)
        self.assertRaises(NotAllowed,
                          UsePortal(imposter['id'], ore['id']).execute, world)


    def test_openerDiesAfterUse(self):
        """
        If the opener dies or is destroyed AFTER a portal is used, it should
        not affect the portal.
        """
        self.usedPortal()

        # kill the opener (send them to the void)
        Move(self.bot['id'], None).execute(self.world)

        # destroy the opener
        self.world.destroy(self.bot['id'])

        self.assertEqual(self.ore['kind'], 'portal', "Should still be a portal")
        self.assertEqual(self.ore['portal_user'], self.lander['id'],
                         "Should still be tied to the lander")



class ListSquaresTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, ListSquares('me'))


    def test_emitters(self):
        self.assertEqual(ListSquares('me').emitters(), [])


    def test_subject(self):
        self.assertEqual(ListSquares('foo').subject(), 'foo')


    def test_execute(self):
        """
        Listing squares should return a list of all the things in the world
        which are squares.  It should include their coordinates and number of
        each kind of thing inside them.
        """
        world = World(MagicMock())
        s1 = world.create('square')['id']
        s2 = world.create('square')['id']
        world.setAttr(s2, 'coordinates', (0, 1))
        
        thing1 = world.create('thing')['id']
        Move(thing1, s2).execute(world)

        output = ListSquares(thing1).execute(world)
        self.assertIn({
            'id': s1,
            'kind': 'square',
            'coordinates': None,
            'contents': {},
        }, output)
        self.assertIn({
            'id': s2,
            'kind': 'square',
            'coordinates': (0, 1),
            'contents': {
                'thing': 1,
            }
        }, output)
        self.assertEqual(len(output), 2)



class AddLockTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, AddLock('me', 'what'))


    def test_emitters(self):
        self.assertEqual(AddLock('me', 'what').emitters(), ['me', 'what'])


    def test_subject(self):
        self.assertEqual(AddLock('foo', 'bar').subject(), 'foo')


    def test_execute(self):
        """
        Locking something should increase the number of 'locks' on the thing.
        """
        world = World(MagicMock())
        thing = world.create('thing')['id']
        box = world.create('box')

        AddLock(thing, box['id']).execute(world)
        self.assertEqual(box['locks'], 1)



class BreakLockTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, BreakLock('me', 'what'))


    def test_emitters(self):
        self.assertEqual(BreakLock('me', 'what').emitters(), ['me', 'what'])


    def test_subject(self):
        self.assertEqual(BreakLock('foo', 'bar').subject(), 'foo')


    def test_execute(self):
        """
        Breaking a lock will reduce the number of locks on a thing.  It can't
        be reduced below 0, though.
        """
        world = World(MagicMock())
        thing = world.create('thing')['id']
        box = world.create('box')

        AddLock(thing, box['id']).execute(world)
        BreakLock(thing, box['id']).execute(world)
        self.assertEqual(box['locks'], 0)

        # make sure it doesn't go negative
        BreakLock(thing, box['id']).execute(world)
        self.assertEqual(box['locks'], 0, "It can't have a negative number "
                         "of locks")



class CreateTeamTest(TestCase):

    timeout = 2


    def test_IAction(self):
        verifyObject(IAction, CreateTeam('me', 'teamA', 'password'))


    def test_emitters(self):
        self.assertEqual(CreateTeam('me', 'teamA', 'password').emitters(), [])


    def test_subject(self):
        self.assertEqual(CreateTeam('foo', 'bar', 'pass').subject(), 'foo')


    def test_execute(self):
        """
        Should set the password for a team.
        """
        auth = FileStoredPasswords(self.mktemp())
        world = World(MagicMock(), auth=auth)
        thing = world.create('thing')
        d = CreateTeam(thing['id'], 'teamA', 'password').execute(world)
        def check(r):
            self.assertEqual(r, 'teamA')
        return d.addCallback(check)



class JoinTeamTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, JoinTeam('me', 'teamA', 'password'))


    def test_emitters(self):
        self.assertEqual(JoinTeam('me', 'teamA', 'password').emitters(), ['me'])


    def test_subject(self):
        self.assertEqual(JoinTeam('foo', 'bar', 'pass').subject(), 'foo')


    @defer.inlineCallbacks
    def test_execute(self):
        """
        Should set the team name if the password matches.
        """
        auth = FileStoredPasswords(self.mktemp())
        world = World(MagicMock(), auth=auth)

        thing = world.create('thing')
        yield CreateTeam(thing['id'], 'teamA', 'password').execute(world)
        yield JoinTeam(thing['id'], 'teamA', 'password').execute(world)
        
        self.assertEqual(thing['team'], 'teamA')


    @defer.inlineCallbacks
    def test_badPassword(self):
        auth = FileStoredPasswords(self.mktemp())
        world = World(MagicMock(), auth=auth)

        thing = world.create('thing')
        yield CreateTeam(thing['id'], 'teamA', 'password').execute(world)
        self.assertFailure(JoinTeam(thing['id'], 'teamA',
                           'not password').execute(world), BadPassword)



















