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

from threading import Lock

from Browser import Browser
from HTTPBase import HTTPBase
from CookieJar import CookieJar

class RequestFactory():
    def __init__(self, core):
        self.lock = Lock()
        self.core = core
        self.cookiejars = {}

    iface = property(lambda self: self.core.config["general"]["download_interface"])

    def getRequest(self, pluginName, account=None):
        self.lock.acquire()

        req = Browser()
        #@TODO proxy stuff, bucket

        if account:
            cj = self.getCookieJar(pluginName, account)
            req.setCookieJar(cj)
        else:
            req.setCookieJar(CookieJar(pluginName))

        self.lock.release()
        return req

    def getURL(self, url, get={}, post={}):
        #a bit to much overhead for single url
        b = Browser()
        #@TODO proxies, iface

        return b.getPage(url, get, post)

    def getCookieJar(self, pluginName, account=None):
        if self.cookiejars.has_key((pluginName, account)):
            return self.cookiejars[(pluginName, account)]

        cj = CookieJar(pluginName, account)
        self.cookiejars[(pluginName, account)] = cj
        return cj

# needs pyreq in global namespace
def getURL(url, get={}, post={}):
    return pyreq.getURL(url, get, post)