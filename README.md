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
wins when it controls all the pylons on the board.

Bots have limited (but renewable) amounts of health and energy.  Using energy,
bots can deal damage to other bots by shooting them with cannons, may heal other
bots by using repair kits, may move to adjacent squares and may capture pylons.
Bots can perform work to gain more energy.

Each square contains a number of material blocks.  Material blocks can be
forged into cannons, repair kits or bot portals.

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


#### Pre-Start Phase

After the board is created, a single bot from each team (the captain) can
connect to the game board and examine the squares to determine where it wants
to start.  Each square may have a different number of material blocks, which
may influence the decision.  At this point, team captain bots may use the
following commands:

    boardDimensions() -> (integer, integer)

    materialCount(square) -> integer
        Return the number of material blocks in a square.
    
    workToCapture(square) -> (nonce='', difficulty, scale)
        Return the work required to capture a square.  `nonce` will always be
        an empty string during the Pre-Start phase.


The game is then started by the server and all bots move to the Captain phase.



#### Captain Phase

Each team captain bot then needs to do the work required to capture an
uncaptured pylon and thereby put themselves on the board.  When in the Captain
phase a captain bot may use the commands available during Pre-Start in addition
to the following commands:

    workToCapture(square) -> (nonce, difficulty, scale)
        Same as in Pre-Start except nonce is no longer an empty string.

    capture(square, solution) -> ()
        Capture a square and put the captain bot on the square.  `solution` is
        a solution to the problem returned by `workToCapture`

Once a bot captures a square, the captain lands on the square and they
immediately move to the In-Play phase.  All other bots that connect will be in
the On-Deck phase.



#### In-Play

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
        material blocks.  It looks like this:

            {
                'bots': {
                    'jim': ...,
                    'bob': ...
                },
                'materials': {
                    'material1': {
                        'use': None,
                        'bot': None,
                        'health': 100,
                    },
                    ...
                },
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



    provisionCannon(material)
        Requires 1 energy.

        Provision the material as a cannon and equip it.

    provisionRepairKit(material)
        Requires 1 energy.

        Provision the material as a repair kit and equip it.

    provisionPortal(material) -> portal_key
        Requires 1 energy.

        Provision the material as a bot portal.  Another bot on your team can
        then enter the game through the portal.



    move(coordinate)
        Requires 2 energy.

        Moves the bot to the identified square (if it is adjacent and the bot
        has enough energy).

    heal(what, name, amount)
        Requires energy proportional to the amount you want to heal.

        1 health requires 1 energy
        3 health requires 2 energy
        6 health requires 3 energy

        This bot must have a repair kit.

    shoot(what, name, damage)
        Requires energy proportional to the amount of damage you want to do.

        1 damage requires 1 energy
        3 damage requires 2 energy
        6 damage requires 3 energy

        This bot must have a cannon.

    shareEnergy(who, amount)
        Lend energy to another bot in this square.

        The chargers used to generate the energy will not be replenished until
        the energy is used by the other bot (or the bot perishes).



#### On-Deck

Bots who connect to the game after the captain has landed on the board will be
in the on-deck phase, waiting for a portal to be provisioned for them.  When
in this phase, bots can do the following:

    usePortal(portal_key)
        Land the bot on the ground and link them to the given portal.  Once
        they land, they will be in the In-Play phase.



Provisioned Materials
-------------------------------------------------------------------------------
Prior to being provisioned, materials are indestructable.  After provisioning,
they are tied to the thing provisioned (cannon, repair kit) and destroying the
material will destroy the tool provisioned from them.  If a portal is destroyed,
the bot that landed with that portal will die.



Work
-------------------------------------------------------------------------------
Most of the moves that bots can make require energy, which is produced by doing
"work", similar to the work done in mining bitcoins.  Capturing squares and
unlocking pylons also require work.

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

