===============================================================================
xatrobot
===============================================================================

[![Build Status](https://secure.travis-ci.org/iffy/xatrobots.png)](http://travis-ci.org/iffy/xatrobots)

Extremely Advanced T-Robot

xatrobot is a game somewhat like AT-Robots, but instead of progamming single
bots, you must create a team of bots.


Gameplay
===============================================================================



Overview
-------------------------------------------------------------------------------
Each game is played on a board of squares.  Bots are members of a team.  Each
square on the board contains a pylon which can be captured by bots.  A team
wins when it has captured all the pylons on the board.

Bots have limited (but renewable) amounts of health and energy.  Using energy,
bots can deal damage to other bots by shooting them with cannons, may heal other
bots by using repair kits, may move to adjacent squares and may capture pylons.
Bots can perform work to gain more energy.

Each square contains a certain amount of ore.  Ore can be converted into
cannons, repair kits or bot portals.

Bots can not communicate on the server.  It is expected that communication and
coordination will happen on the client's computers (that's the whole point).



Board
-------------------------------------------------------------------------------
Each game is played on a board of dimensions Bc x Br.  For instance, here's a
4 x 3 board:

    +---+---+---+---+
    |0,0|   |   |   |
    +---+---+---+---+
    |   |   |   |   |
    +---+---+---+---+
    |   |   |   |3,2|
    +---+---+---+---+

Each square of the board is indexed as shown (top left square is (0,0)).




Phases of the Game
-------------------------------------------------------------------------------
Note that all the hard-coded numbers in this doc should be configurable (energy
requirements, etc...)


#### Pre-Game Phase

After the board is created, a single bot from each team (the captain) can
connect to the game board and examine the squares to determine where it wants
to start.  Each square may have a different amount of ore, which
may influence the decision.  At this point, team captain bots may use the
following commands:

    boardDimensions() -> (integer, integer)

    oreCount(square) -> integer
        Return the amount of ore in the square.
    
    workToLand(square) -> (nonce='', difficulty, scale)
        Return the work required to land on a square.  `nonce` will always be
        an empty string during the Pre-Game Phase.


The game is then started by the server and all bots move to the Landing phase.



#### Landing Phase

Each team captain bot then needs to do the work required to land on the board.
When in the Landing Phase a captain bot may use the commands available during
the Pre-Game Phase in addition to the following commands:

    workToLand(square) -> (nonce, difficulty, scale)
        Same as in Pre-Game Phase except `nonce` is no longer an empty string.

    land(square, solution) -> ()
        Put the captain bot on the square.  `solution` is
        a solution to the problem returned by `workToLand`

Once the captain lands on a square, the captain immediately move to the Play
Phase.  All other bots that connect will be in the On-Deck Phase.



#### Play Phase

When a bot is in play, the following commands are available:

    currentSquare() -> coordinate

    status(bot=None) -> dict
        Requires 0 energy if bot=None, otherwise requires 1 energy.

        If `bot` is None return status of self, otherwise, `bot` should be the
        name of a `bot` in this square.

        {
            'team': string,
            'health': integer,
            'energy': integer,
            'equipment': string,
        }

    charger() -> dict
        Requires 0 energy.

        Once the charger is available, returns a mapping of work to be done to
        generate energy with `charge()`
                
            {'d': 10, 'S': 100, 'n': 'foo'}

        The charger will not be available until the energy produced by the
        charger is used.


    charge(result) -> integer
        Produces 1 energy.

        `result` is an acceptable result of doing the work identified by
        `charger()`.


    look() -> dict of things in the square
        Requires 1 energy.

        Returns a dict of all the things in the square, including bots and
        ore.  It looks like this:

            {
                'jim': <bot dict>,
                'bob': <bot dict>,
                'o-1': <ore dict>,
            }


    pylon() -> dict
        Requires 1 energy.

        Returns a dict describing the current square's pylon:

            {
                'team': None,
                'locks': 1,
                'capture_work': {'d': 10, 'S': 100, 'n': 'foo'},
            }

    unlock(result)
        Requires 3 energy.

        `result` is the result of doing the work defined by
        `pylon()['capture_work']`.

        Unlocks one of the locks on the pylon.  If doing this reduces the number
        of locks to 0, then this bot's team takes control of the pylon and it
        receives 3 locks.

        Returns a dict describing the current square's pylon (same as `pylon()`)

    makeTool(ore, tool_type)
        Requires 1 energy.

        Convert the ore into a tool and equip it.  `tool_type` can be
        'cannon', 'repair kit' or 'portal.'  (Well, it could be any
        string you want, but only those strings will result in useful
        tools.)


    move(coordinate)
        Requires 2 energy.

        Moves the bot to the identified square (if it is adjacent and the bot
        has enough energy).

    heal(what, amount)
        Requires energy proportional to the amount you want to heal.

        1 health requires 1 energy
        3 health requires 2 energy
        6 health requires 3 energy

        This bot must have a 'repair kit' tool.

    shoot(what, damage)
        Requires energy proportional to the amount of damage you want to do.

        1 damage requires 1 energy
        3 damage requires 2 energy
        6 damage requires 3 energy

        This bot must have a 'cannon' tool.

    openPortal(password):
        Requires 1 energy.

        This bot must have a 'portal' tool.

        Open a portal so that an On-Deck bot can use it.

    shareEnergy(who, amount)
        Lend energy to another bot in this square.

        The chargers used to generate the energy will not be replenished until
        the energy is used by the other bot (or the bot perishes).



#### On-Deck Phase

Bots who connect to the game after the captain has landed on the board will be
in the On-Deck Phase, waiting for a portal to be provisioned for them.  When
in this phase, bots can do the following:

    usePortal(bot, password)
        Land the bot on the ground and link them to the portal held open by
        `bot`.  `password` is the password `bot` used when opening the portal.

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

`nonce` or `n`
    a byte string of some non-zero length

`goal` or `G`
    an integer between 0 (easiest) and `MAX_SHA` (hardest).  `MAX_SHA`
    is `0xffffffffffffffffffffffffffffffffffffffff` by default.


The result of a piece of work is any byte string `R` which satisfies this
equation:

    int(sha1(n + R)) > G

Here is a Python function that will determine if a given `R` is an acceptable
result:

    from hashlib import sha1

    def validAnswer(nonce, goal, result):
        result = int(sha1(nonce + result).hexdigest(), 16)
        return result > goal

