xatrobots
==============================================================================

[![Build Status](https://secure.travis-ci.org/iffy/xatrobots.png)](http://travis-ci.org/iffy/xatrobots)

Extremely Advanced T-Robots

xatrobots is a game somewhat like AT-Robots, but instead of progamming single
bots, you must create a team of bots.


Gameplay
==============================================================================



Overview
------------------------------------------------------------------------------
Each game is played on a board of squares.  Bots are members of a team.
Several squares on the board contain a pylon which can be captured by bots.
A team wins when it has captured all the pylons on the board.

Bots have limited (but renewable) amounts of health and energy.  Using energy,
bots can deal damage to other bots by shooting them with cannons, may heal 
other bots by using repair kits, may move to adjacent squares and may capture
pylons. Bots can perform work to gain more energy.

Each square contains a certain amount of ore.  Ore can be converted into
cannons, repair kits or bot portals.

Bots can not communicate on the server.  It is expected that communication
and coordination will happen on the client's computers (that's the whole
point).



Board
------------------------------------------------------------------------------
Each game is played on a board of squares.  Boards aren't necessarily
rectangular.  For instance, here's an example board:

    +---+---+   +---+
    |0,0|   |   |   |
    +---+---+---+---+---+
    |   |   |   |   |   |
    +---+---+---+---+---+
    |   |   |   |3,2|
    +---+---+---+---+
        |1,3|
        +---+


Each square of the board is indexed by a coordinate.  There may not be a square
at (0,0) in every game.  When displaying the board visually, for consistency,
increasing x moves to the right and increasing y moves down (sorry, math).



Game pieces
-------------------------------------------------------------------------------

These are the game pieces:

- Square
- Bot
- Pylon
- Ore
- Lifesource

Following is more detail about them and the attributes they have (including
what a JSON representation of them would look like).


### Square ###

Squares make up the playing field.  Squares can contain Pylons, Bots, Ore and
Lifesources.

    {
      "id": "7b06a48f-6af9-4972-b3ee-5cb9522968e9",
      "object": "square",
      "coordinates": [0, 2],
      "ore_count": 9,
      "pylon_count": 1
    }

Attribute | Details
`id` | UUID of the square.
`object` | Always `"square"`.
`coordinates` | A tuple of the `x` and `y` coordinates of the square.
`ore_count` | The integer amount of ore in this square.
`pylon_count` | The integer number of pylons in this square.



### Bot ###

Bots are used by players to play the game.

    {
      "id": "7b06a48f-6af9-4972-b3ee-5cb9522968e9",
      "object": "bot",
      "hp": 8,
      "team": "A-Team",
      "name": "Joe the Builder",
      "tool": "cannon",
      "energy": 3
    }

Attribute | Details
`id` | UUID of the bot
`object` | Always `"bot"`
`hp` | Integer health remaining.
`team` | String team name
`name` | String bot name
`tool` | String name of the tool currently equipped.
`energy` | Integer amount of energy available for actions.


### Pylon ###

All the pylons must be captured in order to win the game.

    {
      "id": "7b06a48f-6af9-4972-b3ee-5cb9522968e9",
      "object": "pylon",
      "locks": 2,
      "team": "bob",
    }

Attribute | Details
`id` | UUID of the pylon
`object` | Always `"pylon"`
`locks` | Integer number of locks on the pylon.
`team` | The team that currently controls this pylon.  Will be `null` if no team controls it.


### Ore ###

Ore can be forged into tools (such as a cannon, a repair kit or a portal).

    {
      "id": "7b06a48f-6af9-4972-b3ee-5cb9522968e9",
      "object": "ore"
    }

Attribute | Details
`id` | UUID of the ore
`object` | Always `"ore"`


### Lifesource ###

A Lifesource is what replaces a piece of Ore when a tool is made.  If the
Lifesource for a tool is destroyed, the tool is also destroyed.

    {
      "id": "7b06a48f-6af9-4972-b3ee-5cb9522968e9",
      "object": "lifesource",
      "hp": 59
    }

Attribute | Details
`id` | UUID of the lifesource
`object` | Always `"lifesource"`
`hp` | Integer health remaining.



Phases of the Game
-------------------------------------------------------------------------------
Note that all the hard-coded numbers in this doc should be configurable (energy
requirements, etc...)


#### Pre-Game Phase

After the board is created bots can join the game and examine the board to
determine where to start.  Each square may have a different amount of ore,
which may influence the decision.

During this phase, the following commands are available to bots:

- `listSquares()` -> `[<Square>, <Square>, ...]`
  
  List the Squares that make up the board.  Among other things, it will
  show much Ore is in each Square and the coordinates of the Square
   
- `workToLand(square_id)` -> `(nonce, goal)`
  
  Return the goal portion of the work that will be required to land on this
  square during the Landing Phase.  During this phase `nonce` will always
  be `null`.


The game is then started by the server and enters the Landing Phase.



#### Landing Phase

The goal of this phase is to get a bot on the board in a square.  To land,
one of the team's bots must use the `land` command with an acceptable solution
to the work for a square.

In addition to the `listSquares()` command also available during the Pre-Game
Phase, the following commands are available to bots:

- `workToLand(square_id)` -> `(nonce, goal)`
  
  Same as in Pre-Game Phase except `nonce` is now a `string` that can be
  used to do work.

- `land(square_id, solution)`
  
  Put the bot on the designated square.  `solution` must be a solution to the
  problem returned by `workToLand`.

Once *any* bot from a team lands on a square, the bot enters the Play Phase
and the bot's team members enter the On-Deck Phase.  All other teams remain
in the Landing Phase until they have successfully landed a bot in a square.



#### Play Phase

When a bot is in play, the following commands are available:


- `status(bot=None)` -> `<bot>`
  
  Requires 0 energy if bot=None, otherwise requires 1 energy.

  If `bot` is None return status of self, otherwise, `bot` should be the
  id of a `bot` in this square.

      {
          'team': string,
          'health': integer,
          'energy': integer,
          'equipment': string,
      }


- `workToCharge()` -> dict
  
  Requires 0 energy.

  Once the charger is available, returns a piece of work to be done to
  generate energy with `charge()`
            
      Work(nonce, goal)

  The charger will not be available until the previous energy produced by the
  charger is used.


- `charge(solution)`
  
  Produces 1 energy.

  `solution` is an acceptable solution of doing the work identified by
  `charger()`.


- `look()` -> list of things in the square
  
  Requires 1 energy.

  Returns a dict of all the things in the square, including bots and
  ore.  It looks like this:

      {
          'jim': <bot dict>,
          'bob': <bot dict>,
          'o-1': <ore dict>,
      }


- `pylon()` -> dict
  
  Requires 1 energy.

  Returns a dict describing the current square's pylon:

      {
          'team': None,
          'locks': 1,
          'tolock': <Work>,
          'tobreak': <Work>
      }


- `breakLock(solution)`
  
  Requires 3 energy.

  `solution` is the solution of doing the work defined by
  `pylon()['tobreak']`.

  Unlocks one of the locks on the pylon.  If doing this reduces the number
  of locks to 0, then this bot's team takes control of the pylon.


- `addLock(solution)`
  
  Requires 3 energy.

  `solution` is the solution of doing the work defined by
  `pylon()['tolock']`.

  Adds another lock to the pylon.


- `makeTool(ore, tool_type)`
  
  Requires 1 energy.

  Convert the ore into a tool and equip it.  `tool_type` can be
  'cannon', 'repair kit' or 'portal.'  (Well, it could be any
  string you want, but only those strings will result in useful
  tools.)


- `move(square)`
  
  Requires 2 energy.

  Moves the bot to the identified square (if it is adjacent and the bot
  has enough energy).


- `heal(what, amount)`
  
  Requires energy proportional to the amount you want to heal.

  1 health requires 1 energy
  3 health requires 2 energy
  6 health requires 3 energy

  This bot must have a 'repair kit' tool.


- `shoot(what, damage)`

  Requires energy proportional to the amount of damage you want to do.

  1 damage requires 1 energy
  3 damage requires 2 energy
  6 damage requires 3 energy

  This bot must have a 'cannon' tool.


- `openPortal(password)`

  Requires 1 energy.

  This bot must have a 'portal' tool.

  Open a portal so that an On-Deck bot can use it.


- `shareEnergy(who, amount)`

  Lend energy to another bot in this square.

  The chargers used to generate the energy will not be replenished until
  the energy is used by the other bot (or the bot perishes).



#### On-Deck Phase

Bots who connect to the game after the captain has landed on the board will be
in the On-Deck Phase, waiting for a portal to be provisioned for them.  When
in this phase, bots can do the following:

- `usePortal(bot, password)`

  Land the bot on the ground and link them to the portal held open by
  `bot`.  `password` is the password `bot` used when opening the portal.

- `listSquares()`

  Same as in Pre-Game phase.

Once a bot lands, they will be in the Play Phase.



Converted Ore
-------------------------------------------------------------------------------
Prior to being converted into tools, ore is indestructable.  After converting,
the ore becomes a life source for the tool.  Destroying the life source will 
destroy the associated tool.  If a portal is destroyed, the bot that landed
with that portal will die.

Likewise, if a bot carrying a tool dies, the life source used to make the tool
and the portal used to land the bot will both be destroyed and revert back to
ore.


Work
-------------------------------------------------------------------------------
Most of the moves that bots can make require energy, which is produced by doing
"work", similar to the work done in mining bitcoins.  Landing and unlocking and
locking pylons also require work.

A piece of work is defined by a `nonce` and a `goal`:

1. `nonce` or `n`

   a byte string of some non-zero length

2. `goal` or `G`

   an integer between 0 (easiest) and `MAX_SHA` (hardest).  `MAX_SHA`
   is `0xffffffffffffffffffffffffffffffffffffffff` by default.


The result of a piece of work is any byte string `R` which satisfies this
equation:

    int( sha1( n + R ) ) > G

Here is a Python function that will determine if a given `R` is an acceptable
result:

    from hashlib import sha1

    def validAnswer(nonce, goal, result):
        result = int(sha1(nonce + result).hexdigest(), 16)
        return result > goal

