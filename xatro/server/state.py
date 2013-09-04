
from zope.interface import implements

from xatro.server.event import Event
from xatro.server.interface import IEventReceiver


class GameState(object):
    """
    I keep track of the current state of a game by watching an event feed.
    """

    implements(IEventReceiver)


    def __init__(self):
        self.objects = {}


    def eventReceived(self, event):
        """
        An event was received.
        """
        handler = getattr(self, 'handle_%s' % (event.verb,), lambda x:None)
        return handler(
            Event(
                self._mkDict(event.subject),
                event.verb,
                self._mkDict(event.object)))


    def _mkDict(self, obj):
        """
        Ensure that C{obj} is a dictionary (by calling the obj's C{toDict}
        method if there is one)
        """
        return getattr(obj, 'toDict', lambda:obj)()


    def handle_square_added(self, (board, verb, square)):
        self._ensureSquarePresent(square)


    def _ensureSquarePresent(self, square):
        """
        Add a square to the list of objects if it's not already there.
        """
        if square['id'] in self.objects:
            return
        self.objects[square['id']] = {
            'id': square['id'],
            'object': 'square',
            'coordinates': square['coordinates'],
            'contents': {
                'bot': [],
                'lifesource': [],
                'ore': [],
                'pylon': [],
            },
        }


    def handle_joined(self, (bot, verb, board)):
        self.objects[bot['id']] = bot


    def handle_quit(self, (bot, verb, board)):
        self.objects.pop(bot['id'])


    def handle_entered(self, (thing, verb, square)):
        self._ensureSquarePresent(square)
        self.objects[square['id']]['contents'][thing['object']].append(thing['id'])
        self.objects[thing['id']] = thing


    def handle_exited(self, (thing, verb, square)):
        self.objects[square['id']]['contents'][thing['object']].remove(thing['id'])

        # remove non-bots from the object list
        if thing['object'] != 'bot':
            self.objects.pop(thing['id'])


    def handle_pylon_locks(self, (pylon, verb, locks)):
        self.objects[pylon['id']]['locks'] = locks


    def handle_lock_broken(self, (bot, verb, pylon)):
        self.objects[pylon['id']]['locks'] -= 1


    def handle_lock_added(self, (bot, verb, pylon)):
        self.objects[pylon['id']]['locks'] += 1


    def handle_pylon_captured(self, (bot, verb, pylon)):
        self.objects[pylon['id']]['team'] = bot['team']


    def handle_hp_set(self, (thing, verb, hp)):
        self.objects[thing['id']]['hp'] = hp


    def handle_hp(self, (thing, verb, amount)):
        self.objects[thing['id']]['hp'] += amount


    def handle_e_change(self, (bot, verb, amount)):
        self.objects[bot['id']]['energy'] += amount


    def handle_equipped(self, (bot, verb, tool)):
        self.objects[bot['id']]['tool'] = tool['kind']


    def handle_unequipped(self, (bot, verb, ignore)):
        self.objects[bot['id']]['tool'] = None


