# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from datetime import datetime, timedelta
from time import time
import Cookie

# monkey patch for 32 bit systems
def _getdate(future=0, weekdayname=Cookie._weekdayname, monthname=Cookie._monthname):
    dt = datetime.now() + timedelta(seconds=int(future))
    return "%s, %02d %3s %4d %02d:%02d:%02d GMT" % \
           (weekdayname[dt.weekday()], dt.day, monthname[dt.month], dt.year, dt.hour, dt.minute, dt.second)

Cookie._getdate = _getdate


class CookieJar(Cookie.SimpleCookie):
    def getCookie(self, name):
        return self[name].value

    def setCookie(self, domain, name, value, path="/", exp=None, secure="FALSE"):
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
