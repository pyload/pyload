# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from datetime import datetime, timedelta
from time import time
import http.cookies

# monkey patch for 32 bit systems
# def _getdate(future=0, weekdayname=http.cookies._weekdayname, monthname=http.cookies._monthname):
    # dt = datetime.now() + timedelta(seconds=int(future))
    # return "%s, %02d %3s %4d %02d:%02d:%02d GMT" % \
           # (weekdayname[dt.weekday()], dt.day, monthname[dt.month], dt.year, dt.hour, dt.minute, dt.second)

# http.cookies._getdate = _getdate


class CookieJar(http.cookies.SimpleCookie):
    def get_cookie(self, name):
        return self[name].value

    def set_cookie(self, domain, name, value, path="/", exp=None, secure="FALSE"):
        self[name] = value
        self[name]["domain"] = domain
        self[name]["path"] = path

        # Value of expires should be integer if possible
        # otherwise the cookie won't be used
        if not exp:
            expires = time() + 3600 * 24 * 180
        else:
            try:
                expires = int(exp)
            except ValueError:
                expires = exp

        self[name]["expires"] = expires
        if secure == "TRUE":
            self[name]["secure"] = secure
