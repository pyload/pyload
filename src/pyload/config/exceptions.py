# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

from future import standard_library

standard_library.install_aliases()


class AlreadyExistsKeyError(KeyError):
    pass


class InvalidValueError(ValueError):
    pass


class VersionMismatchError(Exception):
    pass
