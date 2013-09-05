from zope.interface import Interface


class IAction(Interface):


    def execute(self, world):
        """
        Do what it means to do this action.  Do not be limited by rules.
        Any rule-limiting will happen prior to this being called.
        
        If the action is to Move, then this moves.
        """


    def emitterId(self):
        """
        Return the world id of the thing doing this action (so that appropriate
        events can be emitted).
        """