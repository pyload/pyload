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
    
    def getAccountInfo(self, user):
        try:
            data = None
            for account in self.accounts.items():
                if account[0] == user:
                    data = account[1]
            if not data:
                raise Exception
            req = self.core.requestFactory.getRequest(self.__name__, user)
            api_url_base = "http://api.rapidshare.com/cgi-bin/rsapi.cgi"
            api_param_prem = {"sub": "getaccountdetails_v1", "type": "prem", "login": user, "password": data["password"], "withcookie": 1}
            src = req.load(api_url_base, cookies=False, get=api_param_prem)
            if src.startswith("ERROR"):
                raise Exception
            fields = src.split("\n")
            info = {}
            for t in fields:
                if not t.strip():
                    continue
                k, v = t.split("=")
                info[k] = v
                
            out = Account.getAccountInfo(self, user)
            restkb = int(info["tskb"])
            maxtraffic = int(info["rapids"])/14 * (5*1024*1024) + restkb
            tmp = {"validuntil":int(info["billeduntil"]), "trafficleft":maxtraffic if int(info["autorefill"]) else restkb, "maxtraffic":maxtraffic}
            out.update(tmp)
            return out
        except:
            return Account.getAccountInfo(self, user)
    
    def login(self, user, data):
        req = self.core.requestFactory.getRequest(self.__name__, user)
        api_url_base = "http://api.rapidshare.com/cgi-bin/rsapi.cgi"
        api_param_prem = {"sub": "getaccountdetails_v1", "type": "prem", "login": user, "password": data["password"], "withcookie": 1}
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
        cj = self.core.requestFactory.getCookieJar(self.__name__, user)
        cj.setCookie("rapidshare.com", "enc", info["cookie"])
            

