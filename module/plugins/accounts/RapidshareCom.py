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

from module.plugins.Account import Account

class RapidshareCom(Account):
    __name__ = "RapidshareCom"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """Rapidshare.com account plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def getAccountInfo(self, name):
        req = self.core.requestFactory.getRequest(self.__name__, name)
        data = None
        for account in self.accounts:
            if account[0] == name:
                data = account
        if not data:
            return
        api_url_base = "http://api.rapidshare.com/cgi-bin/rsapi.cgi"
        api_param_prem = {"sub": "getaccountdetails_v1", "type": "prem", "login": data[0], "password": data[1], "withcookie": 1}
        src = req.load(api_url_base, cookies=False, get=api_param_prem)
        if src.startswith("ERROR"):
            return
        fields = src.split("\n")
        info = {}
        for t in fields:
            if not t.strip():
                continue
            k, v = t.split("=")
            info[k] = v
        out = {"validuntil":None, "login":str(info["accountid"]), "trafficleft":int(info["tskb"]), "type":self.__name__}
        
        return out
    
    def login(self):
        for account in self.accounts:
            req = self.core.requestFactory.getRequest(self.__name__, account[0])
            api_url_base = "http://api.rapidshare.com/cgi-bin/rsapi.cgi"
            api_param_prem = {"sub": "getaccountdetails_v1", "type": "prem", "login": account[0], "password": account[1], "withcookie": 1}
            src = req.load(api_url_base, cookies=False, get=api_param_prem)
            if src.startswith("ERROR"):
                return
            fields = src.split("\n")
            info = {}
            for t in fields:
                if not t.strip():
                    continue
                k, v = t.split("=")
                info[k] = v
            cj = self.core.requestFactory.getCookieJar(self.__name__, account[0])
            cj.setCookie("rapidshare.com", "enc", info["cookie"])
            

