# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

from enum import IntEnum

from future import standard_library

standard_library.install_aliases()


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
    StrList = 15
