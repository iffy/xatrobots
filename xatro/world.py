from uuid import uuid4

from xatro.event import Created, Destroyed, AttrSet, Moved



class World(object):
    """
    I am the world of a single game board.
    """


    def __init__(self, event_receiver):
        self.event_receiver = event_receiver
        self.objects = {}


    def eventReceived(self, event):
        self.event_receiver(event)


    def create(self, kind):
        """
        Create an object of the given kind.
        """
        obj_id = str(uuid4())
        obj = {
            'id': obj_id,
            'kind': kind,
        }
        self.objects[obj_id] = obj
        self.eventReceived(Created(obj_id))
        self.eventReceived(AttrSet(obj_id, 'kind', kind))
        return obj


    def destroy(self, object_id):
        """
        """
        self.move(object_id, None)
        self.objects.pop(object_id)
        self.eventReceived(Destroyed(object_id))


    def get(self, object_id):
        """
        Get an object by id.
        """
        return self.objects[object_id]


    def setAttr(self, object_id, attr_name, value):
        """
        Set the value of an object's attribute.
        """
        self.objects[object_id][attr_name] = value
        self.eventReceived(AttrSet(object_id, attr_name, value))


    def move(self, object_id, new_location_id):
        """
        Move an object into the new location.
        """
        if new_location_id:
            new_location = self._ensureContainer(new_location_id)
            new_location['contents'].append(object_id)

        obj = self.objects[object_id]

        old_location_id = obj.get('location', None)
        if old_location_id:
            old_location = self.objects[old_location_id]
            old_location['contents'].remove(object_id)
        
        obj['location'] = new_location_id

        self.eventReceived(Moved(object_id, old_location_id, new_location_id))


    def _ensureContainer(self, object_id):
        """
        Ensure that the object is a container.
        """
        obj = self.objects[object_id]
        obj['contents'] = []
        return obj

