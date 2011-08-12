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
    __version__ = "0.21"
    __type__ = "account"
    __description__ = """Rapidshare.com account plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")
    
    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        api_url_base = "http://api.rapidshare.com/cgi-bin/rsapi.cgi"
        api_param_prem = {"sub": "getaccountdetails", "type": "prem", "login": user, "password": data["password"], "withcookie": 1}
        src = req.load(api_url_base, cookies=False, get=api_param_prem)
        if src.startswith("ERROR"):
            raise Exception(src)
        fields = src.split("\n")
        info = {}
        for t in fields:
            if not t.strip():
                continue
            k, v = t.split("=")
            info[k] = v

        tmp = {"validuntil":int(info["billeduntil"]), "trafficleft":-1, "maxtraffic":-1}

        return tmp
    
    def login(self, user, data, req):
        api_url_base = "http://api.rapidshare.com/cgi-bin/rsapi.cgi"
        api_param_prem = {"sub": "getaccountdetails", "type": "prem", "login": user, "password": data["password"], "withcookie": 1}
        src = req.load(api_url_base, cookies=False, get=api_param_prem)
        if src.startswith("ERROR"):
            raise Exception(src+"### Note you have to use your account number for login, instead of name.")
        fields = src.split("\n")
        info = {}
        for t in fields:
            if not t.strip():
                continue
            k, v = t.split("=")
            info[k] = v
        cj = self.getAccountCookies(user)
        cj.setCookie("rapidshare.com", "enc", info["cookie"])
            

