# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library

try:
    from enum import IntEnum
except ImportError:
    from aenum import IntEnum

standard_library.install_aliases()


class Connection(IntEnum):
    All = 0
    Resumable = 1
    Secure = 2
