from twisted.trial.unittest import TestCase
from zope.interface.verify import verifyObject

from mock import MagicMock

from xatro.interface import IAction
from xatro.world import World
from xatro.action import Move, Charge, ShareEnergy, ConsumeEnergy, Shoot
from xatro.action import Repair, Look
from xatro.event import Destroyed
from xatro.error import NotEnoughEnergy, Invulnerable



class MoveTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, Move('foo', 'bar'))


    def test_emitters(self):
        self.assertEqual(Move('foo', 'bar').emitters(), ['foo'])


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



class ChargeTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, Charge('foo'))


    def test_emitters(self):
        self.assertEqual(Charge('foo').emitters(), ['foo'])


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



class RepairTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, Repair('foo', 'bar', 3))


    def test_emitters(self):
        self.assertEqual(Repair('foo', 'bar', '3').emitters(), ['foo', 'bar'])


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



class LookTest(TestCase):


    def test_IAction(self):
        verifyObject(IAction, Look('foo'))


    def test_emitters(self):
        self.assertEqual(Look('foo').emitters(), ['foo'])


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






