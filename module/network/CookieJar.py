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

from cookielib import CookieJar as PyCookieJar
from cookielib import Cookie


class CookieJar(PyCookieJar):
    def __init__(self, pluginName=None, account=None):
        PyCookieJar.__init__(self)
        self.plugin = pluginName
        self.account = account


    def getCookie(self, name):
        print "getCookie not implemented!"
        return None

    def setCookie(self, domain, name, value, path="/"):
        c = Cookie(version=0, name=name, value=value, port=None, port_specified=False,
                   domain=domain, domain_specified=False,
                   domain_initial_dot=(domain.startswith(".")), path=path, path_specified=True,
                   secure=False, expires=None, discard=True, comment=None,
                   comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        self.set_cookie(c)