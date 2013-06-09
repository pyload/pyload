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

    @author: RaNaN
"""

from types import MethodType

from module.plugins.Account import Account
from module.common.json_layer import json_loads

class WuploadCom(Account):
    __name__ = "WuploadCom"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """wupload.com account plugin"""
    __author_name__ = ("RaNaN", "Paul King")
    __author_mail__ = ("RaNaN@pyload.org", "")

    API_URL = "http://api.wupload.com"

    def init(self):
        fs = self.core.pluginManager.loadClass("accounts", "FilesonicCom")

        methods = ["loadAccountInfo", "login"]
        #methods to bind from fs

        for m in methods:
            setattr(self, m, MethodType(fs.__dict__[m], self, WuploadCom))

    def getDomain(self, req):
        xml = req.load(self.API_URL + "/utility?method=getWuploadDomainForCurrentIp&format=json",
                       decode=True)
        return json_loads(xml)["FSApi_Utility"]["getWuploadDomainForCurrentIp"]["response"]