
from pyload.Api import Input, InputType
from pyload.utils import decode, to_bool

# Maps old config formats to new values
input_dict = {
    "int": InputType.Int,
    "bool": InputType.Bool,
    "time": InputType.Time,
    "file": InputType.File,
    "folder": InputType.Folder
}


def to_input(typ):
    """ Converts old config format to input type"""
    return input_dict.get(typ, InputType.Text)


def from_string(value, typ=None):
    """ cast value to given type, unicode for strings """

    # value is no string
    if not isinstance(value, basestring):
        return value

    value = decode(value)

    if typ == InputType.Int:
        return int(value)
    elif typ == InputType.Bool:
        return to_bool(value)
    elif typ == InputType.Time:
        if not value: value = "0:00"
        if not ":" in value: value += ":00"
        return value
    else:
        return value