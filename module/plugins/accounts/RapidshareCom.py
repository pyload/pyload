# -*- coding: utf-8 -*-

from module.plugins.Account import Account


class RapidshareCom(Account):
    __name__    = "RapidshareCom"
    __type__    = "account"
    __version__ = "0.22"

    __description__ = """Rapidshare.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        api_url_base = "http://api.rapidshare.com/cgi-bin/rsapi.cgi"
        api_param_prem = {"sub": "getaccountdetails", "type": "prem", "login": user,
                          "password": data['password'], "withcookie": 1}
        html = req.load(api_url_base, cookies=False, get=api_param_prem)
        if html.startswith("ERROR"):
            raise Exception(html)
        fields = html.split("\n")
        info = {}
        for t in fields:
            if not t.strip():
                continue
            k, v = t.split("=")
            info[k] = v

        validuntil = int(info['billeduntil'])
        premium = True if validuntil else False

        tmp = {"premium": premium, "validuntil": validuntil, "trafficleft": -1, "maxtraffic": -1}

        return tmp


    def login(self, user, data, req):
        api_url_base = "http://api.rapidshare.com/cgi-bin/rsapi.cgi"
        api_param_prem = {"sub": "getaccountdetails", "type": "prem", "login": user,
                          "password": data['password'], "withcookie": 1}
        html = req.load(api_url_base, cookies=False, get=api_param_prem)
        if html.startswith("ERROR"):
            raise Exception(html + "### Note you have to use your account number for login, instead of name")
        fields = html.split("\n")
        info = {}
        for t in fields:
            if not t.strip():
                continue
            k, v = t.split("=")
            info[k] = v
        cj = self.getAccountCookies(user)
        cj.setCookie(".rapidshare.com", "enc", info['cookie'])
