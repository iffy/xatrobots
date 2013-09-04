from collections import namedtuple


Created = namedtuple('Created', ['id'])
Destroyed = namedtuple('Destroyed', ['id'])
AttrSet = namedtuple('AttrSet', ['id', 'name', 'value'])
Moved = namedtuple('Moved', ['object_id', 'from_location', 'to_location'])
