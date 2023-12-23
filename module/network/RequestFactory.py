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
from Bucket import Bucket
from HTTPRequest import HTTPRequest
from CookieJar import CookieJar

from XDCCRequest import XDCCRequest


class RequestFactory():
    def __init__(self, core):
        self.lock = Lock()
        self.core = core
        self.bucket = Bucket()
        self.updateBucket()
        self.cookiejars = {}

    def iface(self):
        return self.core.config["download"]["interface"]

    def getRequest(self, pluginName, account=None, type="HTTP", **kwargs):
        self.lock.acquire()

        options = self.getOptions()
        options.update(kwargs)  # submit kwargs as additional options

        if type == "XDCC":
            req = XDCCRequest(self.bucket, options)

        else:
            req = Browser(self.bucket, options)

            if account:
                cj = self.getCookieJar(pluginName, account)
                req.setCookieJar(cj)
            else:
                req.setCookieJar(CookieJar(pluginName))

        self.lock.release()
        return req

    def getHTTPRequest(self, **kwargs):
        """ returns a http request, dont forget to close it ! """
        options = self.getOptions()
        options.update(kwargs)  # submit kwargs as additional options
        return HTTPRequest(CookieJar(None), options)

    def getURL(self, *args, **kwargs):
        """ see HTTPRequest for argument list """
        h = HTTPRequest(None, self.getOptions())
        try:
            rep = h.load(*args, **kwargs)
        finally:
            h.close()

        return rep

    def getCookieJar(self, pluginName, account=None):
        if (pluginName, account) in self.cookiejars:
            return self.cookiejars[(pluginName, account)]

        cj = CookieJar(pluginName, account)
        if account:
            self.cookiejars[(pluginName, account)] = cj
        return cj

    def removeCookieJar(self, plugin_name, account):
        self.cookiejars.pop((plugin_name, account), None)

    def getProxies(self):
        """ returns proxy related options """
        proxy = self.core.config["proxy"]
        if not proxy["proxy"]:
            return {}
        else:
            proxy_type = proxy["type"]
            socks_resolve_dns = proxy["socksResolveDns"]
            proxy_username = proxy["username"] or None
            proxy_password = proxy["password"] or None

            return {
                "type"    : proxy_type,
                "socksResolveDns": socks_resolve_dns,
                "address" : proxy["address"],
                "port"    : proxy["port"],
                "username": proxy_username,
                "password": proxy_password,
            }


    def getOptions(self):
        """ returns options needed for pycurl """
        return {"interface": self.iface(),
                "proxies"  : self.getProxies(),
                "ipv6"     : self.core.config["download"]["ipv6"]}

    def updateBucket(self):
        """ set values in the bucket according to settings"""
        if not self.core.config["download"]["limit_speed"]:
            self.bucket.setRate(-1)
        else:
            self.bucket.setRate(self.core.config["download"]["max_speed"] * 1024)


# needs pyreq in global namespace
def getURL(*args, **kwargs):
    return pyreq.getURL(*args, **kwargs)


def getRequest(*args, **kwargs):
    return pyreq.getHTTPRequest()
