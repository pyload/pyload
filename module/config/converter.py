# -*- coding: utf-8 -*-

from module.utils import decode

def to_string(value):
    return str(value) if not isinstance(value, basestring) else value

# cast value to given type, unicode for strings
def from_string(value, typ=None):

    # value is no string
    if not isinstance(value, basestring):
        return value

    value = decode(value)

    if typ == "int":
        return int(value)
    elif typ == "bool":
        return True if value.lower() in ("1", "true", "on", "an", "yes") else False
    elif typ == "time":
        if not value: value = "0:00"
        if not ":" in value: value += ":00"
        return value
    else:
        return value