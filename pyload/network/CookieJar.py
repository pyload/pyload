# -*- coding: utf-8 -*-
# @author: RaNaN

import Cookie
import datetime
import time


# monkey patch for 32 bit systems
def _getdate(future=0, weekdayname=Cookie._weekdayname, monthname=Cookie._monthname):
    dt = datetime.datetime.now() + datetime.timedelta(seconds=int(future))
    return "%s, %02d %3s %4d %02d:%02d:%02d GMT" % \
           (weekdayname[dt.weekday()], dt.day, monthname[dt.month], dt.year, dt.hour, dt.minute, dt.second)

Cookie._getdate = _getdate


class CookieJar(Cookie.SimpleCookie):

    def getCookie(self, name):
        return self[name].value

    def addPycurlCookies(self, clist):
        for c in clist:
            splitted = c.split("\t")
            domain = splitted[0]
            path = splitted[2]
            name = splitted[5]
            value = splitted[6]

            self.setCookie(domain, name, value, path)

    def getAsPycurlCookies(self):
        cookies = list()

        for cookie in self:
            cstr = "\t".join((self[cookie]["domain"], "FALSE", self[cookie]["path"], self[cookie]["secure"],
                              str(self[cookie]["expires"]), cookie, self[cookie].value))
            cookies.append(cstr)

        return cookies

    def setCookie(self, domain, name, value, path="/", exp=None, secure="FALSE"):
        self[name] = value
        self[name]['domain'] = domain
        self[name]['path']   = path

        # Value of expires should be integer if possible
        # otherwise the cookie won't be used
        if not exp:
            expires = time.time() + 3600 * 24 * 180
        else:
            try:
                expires = int(exp)
            except ValueError:
                expires = exp

        self[name]['expires'] = expires

        self[name]['secure'] = secure
