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

