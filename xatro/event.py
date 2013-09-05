from collections import namedtuple


Created = namedtuple('Created', ['id'])
Destroyed = namedtuple('Destroyed', ['id'])
AttrSet = namedtuple('AttrSet', ['id', 'name', 'value'])
ItemAdded = namedtuple('ItemAdded', ['id', 'name', 'added_value'])
ItemRemoved = namedtuple('ItemRemoved', ['id', 'name', 'removed_value'])

ActionPerformed = namedtuple('ActionPerformed', ['action'])