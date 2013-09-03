from zope.interface import Interface, Attribute


class IEventReceiver(Interface):


    def eventReceived(event):
        """
        An event happened.
        """



class IKillable(Interface):


    def damage(amount):
        """
        Damage the thing.
        """


    def revive(amount):
        """
        Heal the thing a certain amount
        """


    def hitpoints():
        """
        Return the number of hitpoints this thing has.
        """


    def kill():
        """
        Kill a thing dead.
        """


    def destroyed():
        """
        Return a deferred which fires when I'm killed.
        """


class ILocatable(Interface):


    id = Attribute("Unique string ID of thing.")

    square = Attribute("Square thing is in")



class IWorkMaker(Interface):


    def workFor(worker, action, target=None):
        """
        Return the Work required by C{worker} to do the C{action} to C{target}.
        """


    def validSolution(work, solution):
        """
        Return C{True} if the solution is a valid one for the work.
        """



class IGameRules(IEventReceiver):


    def assertSolution(solution, work):
        """
        Assert that the given solution solves the work requirement.
        """


    def workRequirement(bot, action, *args, **kwargs):
        """
        Return the L{Work} required before a bot can perform the given action.

        @rtype: L{Work}
        """


    def energyRequirement(bot, action, *args, **kwargs):
        """
        Return the amount of energy that is required of a bot to perform the
        given action.

        @rtype: integer
        """


    def energyToHitpoints(bot, action, target, energy):
        """
        Return the number of hitpoints to be added/removed when a bot does
        this action (shoot, heal) on the given target with the given amount
        of energy.

        @rtype: integer
        """


    def isAllowed(bot, action, *args, **kwargs):
        """
        Raises an exception if the action is not allowed,
        otherwise returns None.
        """



class IGamePiece(Interface):


    game = Attribute("Reference to the game")


class IDictable(Interface):


    def toDict():
        """
        Convert this object into a dictionary representation.
        """



