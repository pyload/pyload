# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import time
from http.cookies import SimpleCookie

from future import standard_library
from future.builtins import int

from pyload.utils.convert import to_str

standard_library.install_aliases()


class CookieJar(SimpleCookie):

    __slots__ = []

    EXPIRE_TIME = 180 * 24 * 3600

    def set(self, domain, name, value, path='/', expires=None, secure=False,
            tailmatch=False):
        self.__dict__[name] = dict()
        self.__dict__[name]['id'] = to_str(value)
        self.__dict__[name]['domain'] = to_str(domain)
        self.__dict__[name]['tailmatch'] = 'TRUE' if tailmatch else 'FALSE'
        self.__dict__[name]['path'] = to_str(path)
        self.__dict__[name]['secure'] = 'TRUE' if secure else 'FALSE'
        self.__dict__[name]['expires'] = int(
            expires or time.time() + self.EXPIRE_TIME)
