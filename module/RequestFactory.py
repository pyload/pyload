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
from module.network.XdccRequest import XdccRequest
from module.network.FtpRequest import FtpRequest
from time import time

class RequestFactory():
    def __init__(self, core):
        self.lock = Lock()
        self.core = core
        self.requests = []
        self.cookiejars = []
    
    def getRequest(self, pluginName, account=None, type="HTTP"):
        self.lock.acquire()
        if type == "HTTP":
            iface = self.core.config["general"]["download_interface"]
            req = Request(interface=str(iface))
            if account:
                cj = self.getCookieJar(pluginName, account)
                req.setCookieJar(cj)
            else:
                req.setCookieJar(CookieJar(pluginName))
            
        elif type == "XDCC":
            req = XdccRequest()
            
        elif type == "FTP":
            req = FtpRequest()
            
        self.requests.append((pluginName, account, req))
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
        cj = CookieJar(plugin, account)
        self.cookiejars.append(cj)
        return cj
    
class CookieJar():
    def __init__(self, plugin, account=None):
        self.cookies = {}
        self.plugin = plugin
        self.account = account
    
    def addCookies(self, clist):
        for c in clist:
            name = c.split("\t")[5]
            self.cookies[name] = c
    
    def getCookies(self):
        return self.cookies.values()
    
    def parseCookie(self, name):
        return self.cookies[name].split("\t")[6]
    
    def getCookie(self, name):
        return self.parseCookie(name)
    
    def setCookie(self, domain, name, value, path="/", exp=time()+3600*24*180):
        s = ".%s	TRUE	%s	FALSE	%s	%s	%s" % (domain, path, exp, name, value)
        self.cookies[name] = s
