==============================================================================
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

