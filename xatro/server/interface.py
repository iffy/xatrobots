from zope.interface import Interface


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
        Kill this thing dead.  (For disconnections, mostly)
        """