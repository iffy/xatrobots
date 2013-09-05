from zope.interface import Interface


class IAction(Interface):


    def execute(world):
        """
        Do what it means to do this action.  Do not be limited by rules.
        Any rule-limiting will happen prior to this being called.
        
        If the action is to Move, then this moves.
        """


    def emitters():
        """
        Return a list of the world ids of the things that should emit this
        event.
        """



class IEngine(Interface):


    def execute(world, action):
        """
        Determine if the action is okay, then do it if it is.  Return the
        result of the action.
        """



class IXatroEngine(Interface):


    def workRequirement(world, action):
        """
        Return the work required to do an action.
        """


    def energyRequirement(world, action):
        """
        Return the energy required to do an action.
        """


    def isAllowed(world, action):
        """
        Raise an exception if this action is not allowed.
        """
