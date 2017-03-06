# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals

from builtins import object

from enum import IntFlag
from future import standard_library

standard_library.install_aliases()

__all__ = ['Input', 'InputType']


class Input(object):
    __slots__ = ['type', 'default_value', 'data']

    def __init__(self, type_=None, default_value=None, data=None):
        self.type = type_
        self.default_value = default_value
        self.data = data

    def __str__(self):
        return "<{0} {1}>".format(self.__class__.__name__, ", ".join(
            "{0}={1}".format(k, getattr(self, k)) for k in self.__slots__))


class InputType(IntFlag):
    NA = 0
    Text = 1
    Int = 2
    File = 3
    Folder = 4
    Textbox = 5
    Password = 6
    Time = 7
    TimeSpan = 8
    ByteSize = 9
    Bool = 10
    Click = 11
    Select = 12
    Multiple = 13
    List = 14
    PluginList = 15
    Table = 16
    Port = 17
