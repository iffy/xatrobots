from twisted.web.static import File
from twisted.internet import defer
from klein import Klein

import json

from xatro.transformer import DictTransformer
from xatro.state import State



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
        self._state = State()
        self._transformer = DictTransformer()
        self.static_root = static_root
        self._observers = []


    def eventReceived(self, event):
        """
        Game event received.
        """
        self._state.eventReceived(event)
        message = self._transformer.transform(event)
        self.sendMessage('ev', json.dumps(message))


    @app.route('/game')
    def html(self, request):
        """
        HTML that will source /current_state and /events for more information.
        """
        return File(self.static_root.child('game.html').path)


    @app.route('/events')
    def events(self, request):
        """
        SSE stream of events.
        """
        self._observers.append(request)
        request.notifyFinish().addCallback(self._removeRequest)

        request.setHeader('Content-Type', 'text/event-stream')
        # send the current state of the game.
        request.write(self.sse('state', json.dumps(self._state.state)))
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

