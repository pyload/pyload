# -*- coding: utf-8 -*-

from module.plugins.Account import Account


class RapidshareCom(Account):
    __name__ = "RapidshareCom"
    __type__ = "account"
    __version__ = "0.22"

    __description__ = """Rapidshare.com account plugin"""
    __author_name__ = "mkaay"
    __author_mail__ = "mkaay@mkaay.de"


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        api_url_base = "http://api.rapidshare.com/cgi-bin/rsapi.cgi"
        api_param_prem = {"sub": "getaccountdetails", "type": "prem", "login": user,
                          "password": data['password'], "withcookie": 1}
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

        validuntil = int(info['billeduntil'])
        premium = True if validuntil else False

        tmp = {"premium": premium, "validuntil": validuntil, "trafficleft": -1, "maxtraffic": -1}

        return tmp

    def login(self, user, data, req):
        api_url_base = "http://api.rapidshare.com/cgi-bin/rsapi.cgi"
        api_param_prem = {"sub": "getaccountdetails", "type": "prem", "login": user,
                          "password": data['password'], "withcookie": 1}
        src = req.load(api_url_base, cookies=False, get=api_param_prem)
        if src.startswith("ERROR"):
            raise Exception(src + "### Note you have to use your account number for login, instead of name.")
        fields = src.split("\n")
        info = {}
        for t in fields:
            if not t.strip():
                continue
            k, v = t.split("=")
            info[k] = v
        cj = self.getAccountCookies(user)
        cj.setCookie("rapidshare.com", "enc", info['cookie'])
