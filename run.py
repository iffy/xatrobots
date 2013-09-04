from twisted.python.filepath import FilePath
from twisted.internet import task

from xatro.web.observatory import GameObserver
from xatro.server.event import Event
from xatro.server.game import Game, StaticRules
from xatro.server.state import GameState
from xatro.server.player import BotPlayer
from xatro.server.board import Pylon, Ore

import random


def buildSquares(game, ore_min=2, ore_max=8):
    board = game.board
    for i in xrange(3):
        for j in xrange(3):
            s = board.addSquare((i, j))
            s.addThing(Pylon())
            for o in xrange(random.randint(ore_min, ore_max)):
                s.addThing(Ore())

# make the game
game = Game()
rules = StaticRules()
game.setRules(rules)
game.mkBoard()

# hook up the web_app
web_app = GameObserver(FilePath('templates'))
game.subscribe(web_app.eventReceived)

# make the board
buildSquares(game)

# XXX dummy
def hey(game):
    square = random.choice(game.board.squares.values())
    pylon = square.contents(Pylon)[0]
    pylon.setLocks(pylon.locks + 1)
    print 'boosted locks'

    #game.board.eventReceived(Event(Pylon))


lc = task.LoopingCall(hey, game)
lc.start(2)

# run the webserver
web_app.app.run('127.0.0.1', 8070)