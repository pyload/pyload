# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

from future import standard_library

standard_library.install_aliases()


class AlreadyExistsKeyError(KeyError):

    __slots__ = []


class InvalidValueError(ValueError):

    __slots__ = []


class VersionMismatchError(Exception):

    __slots__ = []
