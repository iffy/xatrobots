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
