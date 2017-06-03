# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

from future import standard_library

standard_library.install_aliases()
try:
    from enum import IntEnum
except ImportError:
    from aenum import IntEnum


class InputType(IntEnum):
    NA = 0
    Bool = 1
    Int = 2
    Float = 3
    Octal = 4
    Str = 5
    Bytes = 6
    Size = 7
    File = 8
    Folder = 9
    Password = 10
    Time = 11
    Click = 12
    Address = 13
    Tristate = 14
    StrList = 15
