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
from tempfile import NamedTemporaryFile

class RequestFactory():
    def __init__(self, core):
        self.lock = Lock()
        self.core = core
        self.requests = []
    
    def getRequest(self, pluginName, account=None):
        self.lock.acquire()
        cookieFile = None
        for req in self.requests:
            if req[0:2] == (pluginName, account):
                cookieFile = req[2].cookieFile
                break
        
        if not cookieFile:
            name = pluginName
            if account:
                name += "_"
                name += account
            th = NamedTemporaryFile(mode="w", prefix="pyload_cookies_%s" % name, delete=False)
            cookieFile = th.name
            th.close()
        
        req = Request(cookieFile)
        self.requests.append((pluginName, account, req))
        self.lock.release()
        return req
    
    def clean(self):
        self.lock.acquire()
        for req in self.requests:
            req[2].clean()
        self.lock.release()
