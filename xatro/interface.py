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