# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import time
from builtins import int, str
from http.cookies import SimpleCookie

from future import standard_library

standard_library.install_aliases()


# monkey patch for 32 bit systems
# def _getdate(future=0, weekdayname=http.cookies._weekdayname, monthname=http.cookies._monthname):
# dt = datetime.now() + timedelta(seconds=int(future))
# return "{}, %02d %3s %4d %02d:%02d:%02d GMT" % (weekdayname[dt.weekday()], dt.day, monthname[dt.month], dt.year, dt.hour, dt.minute, dt.second)

# http.cookies._getdate = _getdate


class CookieJar(SimpleCookie):

    __slots__ = ['EXPIRE_TIME']

    EXPIRE_TIME = 180 * 24 * 3600

    def set(self, domain, name, value, path='/', expires=None, secure=False,
            tailmatch=False):
        self.__dict__[name] = str(value)
        self.__dict__[name]['domain'] = str(domain)
        self.__dict__[name]['tailmatch'] = 'TRUE' if tailmatch else 'FALSE'
        self.__dict__[name]['path'] = str(path)
        self.__dict__[name]['secure'] = 'TRUE' if secure else 'FALSE'
        self.__dict__[name]['expires'] = int(
            expires or time.time() + self.EXPIRE_TIME)
