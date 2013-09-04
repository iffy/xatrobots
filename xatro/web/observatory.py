from twisted.web.static import File
from twisted.internet import defer
from klein import Klein

import json

from xatro.server.state import GameState



def toDictObjects(obj):
    func = getattr(obj, 'toDict', None)
    if func:
        return obj.toDict()
    else:
        raise TypeError(obj)


def toJson(thing):
    return json.dumps(thing, default=toDictObjects)



class GameObserver(object):
    """
    I observe a single game and maintain my own copy of the state of the game.
    """

    app = Klein()


    def __init__(self, static_root):
        self._state = GameState()
        self.static_root = static_root
        self._observers = []


    def eventReceived(self, event):
        """
        Game event received.
        """
        self._state.eventReceived(event)
        self.sendMessage('ev', toJson(event))


    @app.route('/game')
    def html(self, request):
        """
        HTML that will source /current_state and /events for more information.
        """
        return File(self.static_root.child('game.html').path)


    @app.route('/current_state')
    def current_state(self, request):
        """
        Return the current state of the game.
        """
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(self._state.objects)


    @app.route('/events')
    def events(self, request):
        """
        SSE stream of events.
        """
        self._observers.append(request)
        request.notifyFinish().addCallback(self._removeRequest)

        request.setHeader('Content-Type', 'text/event-stream')
        request.write(self.sse('a', 'hey'))
        return defer.Deferred()


    def sse(self, key, value):
        return 'event: %s\ndata: %s\n\n' % (key, value)


    def sendMessage(self, key, value):
        """
        Send an SSE-formatted message to all requests.
        """
        msg = self.sse(key, value)
        for o in self._observers:
            o.write(msg)


    def _removeRequest(self, request):
        self._observers.remove(request)

