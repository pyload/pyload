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
    
    @author: mkaay
"""

from threading import Lock
from module.network.Request import Request
from module.network.Browser import Browser
from module.network.XdccRequest import XdccRequest
from module.network.FtpRequest import FtpRequest
from time import time
from cookielib import CookieJar
from cookielib import Cookie

class RequestFactory():
    def __init__(self, core):
        self.lock = Lock()
        self.core = core
        self.requests = []  #seems useless
        self.cookiejars = []
        self.iface = self.core.config["general"]["download_interface"]
    
    def getRequest(self, pluginName, account=None, type="HTTP"):
        self.lock.acquire()
        if type == "HTTP":
            req = Browser()
            if account:
                cj = self.getCookieJar(pluginName, account)
                req.setCookieJar(cj)
            else:
                req.setCookieJar(PyLoadCookieJar(pluginName))
            
        elif type == "XDCC":
            req = XdccRequest()
            
        elif type == "FTP":
            req = FtpRequest()
            
        #self.requests.append((pluginName, account, req))
        self.lock.release()
        return req

    def clean(self):
        self.lock.acquire()
        for req in self.requests:
            req[2].clean()
        self.lock.release()
    
    def getCookieJar(self, plugin, account=None):
        for cj in self.cookiejars:
            if (cj.plugin, cj.account) == (plugin, account):
                return cj
        cj = PyLoadCookieJar(plugin, account)
        self.cookiejars.append(cj)
        return cj
    
class PyLoadCookieJar(CookieJar):
    def __init__(self, plugin, account=None):
        CookieJar.__init__(self)
        self.cookies = {}
        self.plugin = plugin
        self.account = account

    def __del__(self):
        if hasattr(self, "cookies"):
            del self.cookies
        if hasattr(self, "plugin"):
            del self.plugin
    
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
