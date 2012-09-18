# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: mkaay, RaNaN
"""

from time import time

class CookieJar():
    def __init__(self, pluginname):
        self.cookies = {}
        self.pluginname = pluginname

    def __repr__(self):
        return ("<CookieJar plugin=%s>\n\t" % self.pluginname) + "\n\t".join(self.cookies.values())

    def addCookies(self, clist):
        for c in clist:
            name = c.split("\t")[5]
            self.cookies[name] = c

    def getCookies(self):
        return self.cookies.values()

    def getCookie(self, name):
        if name in self.cookies:
            return self.cookies[name].split("\t")[6]
        else:
            return None

    def setCookie(self, domain, name, value, path="/", exp=None):
        if not exp: exp = time() + 3600 * 24 * 180

        # dot makes it valid on all subdomains
        s = ".%s	TRUE	%s	FALSE	%s	%s	%s" % (domain.strip("."), path, exp, name, value)
        self.cookies[name] = s

    def clear(self):
        self.cookies = {}