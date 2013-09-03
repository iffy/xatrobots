from twisted.python.filepath import FilePath
from twisted.internet import task

from xatro.server.event import Event
from xatro.web.observatory import GameObserver
from xatro.server.game import Game, StaticRules
from xatro.server.player import BotPlayer


def event(game):
    from xatro.server.board import Bot, Ore
    game.board.eventReceived(Event(Bot('jim', 'bob'), 'ate', Ore()))

game = Game()
rules = StaticRules()
game.setRules(rules)
game.mkBoard()

lc = task.LoopingCall(event, game)
lc.start(2)

app = GameObserver(game, FilePath('templates'))
app.app.run('127.0.0.1', 8070)