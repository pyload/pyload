# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import os

from builtins import bytes, int, str

from gettext import gettext

from future import standard_library
standard_library.install_aliases()

from pyload.utils import convert, parse
from pyload.utils.layer.legacy.collections_ import namedtuple

from .types import Input, InputType


__all__ = ['from_string', 'to_configdata', 'to_input']


# Maps old config formats to new values
input_dict = {
    'int': InputType.Int,
    'bool': InputType.Bool,
    'time': InputType.Time,
    'file': InputType.File,
    'list': InputType.List,
    'folder': InputType.Folder
}

def to_input(type_):
    """
    Converts old config format to input type.
    """
    return input_dict.get(type_, InputType.Text)


ConfigData = namedtuple("ConfigData", "label description input")

def to_configdata(entry):
    if len(entry) != 4:
        raise ValueError("Config entry must be of length 4")

    # Values can have different roles depending on the two config formats
    conf_name, type_label, label_desc, default_input = entry

    # name, label, desc, input
    if isinstance(default_input, Input):
        _input = default_input
        conf_label = type_label
        conf_desc = label_desc
    # name, type, label, default
    else:
        _input = Input(to_input(type_label))
        _input.default_value = from_string(default_input, _input.type)
        conf_label = label_desc
        conf_desc = ""

    return conf_name, ConfigData(
        gettext(conf_label), gettext(conf_desc), _input)


# TODO: Rewrite...
def from_string(value, type_=None):
    """
    Cast value to given type, unicode for strings.
    """
    if not isinstance(value, str):
        return value
    res = value = value.strip()
    if type_ == InputType.File:
        res = os.path.abspath(os.path.expanduser(value)) if value else None
    elif type_ == InputType.Folder:
        res = os.path.abspath(
            os.path.dirname(
                os.path.expanduser(value))) if value else None
    elif type_ == InputType.Int:
        res = convert.to_int(value, 0)
    elif type_ == InputType.Port:
        res = convert.to_int(value)
    elif type_ == InputType.Bool:
        res = parse.boolean(value)
    elif type_ == InputType.Time:
        if not value:
            value = "0:00"
        if ":" not in value:
            value += ":00"
        res = value
    return res
