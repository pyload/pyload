# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from enum import IntEnum

from future import standard_library

standard_library.install_aliases()


class Connection(IntEnum):
    All = 0
    Resumable = 1
    Secure = 2
