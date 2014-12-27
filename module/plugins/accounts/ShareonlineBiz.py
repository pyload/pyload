# -*- coding: utf-8 -*-

from module.plugins.Account import Account


class ShareonlineBiz(Account):
    __name__    = "ShareonlineBiz"
    __type__    = "account"
    __version__ = "0.27"

    __description__ = """Share-online.biz account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def api_response(self, user, req):
        return req.load("http://api.share-online.biz/cgi-bin",
                        get={'q': "userdetails", 'aux': "traffic", "username": user, "password": self.accounts[user]['password']})


    def loadAccountInfo(self, user, req):
        premium     = False
        validuntil  = None
        trafficleft = -1
        maxtraffic  = 100 * 1024 * 1024 * 1024  #: 100 GB

        api = {}
        for line in self.api_response(user, req).splitlines():
            if "=" in line:
                key, value = line.split("=")
                api[key] = value

        self.logDebug(api)

        for key in ("dl", "a"):
            if key not in api:
                continue

            if api['group'] != "Sammler":
                premium = True

            if api[key].lower() != "not_available":
                req.cj.setCookie("share-online.biz", key, api[key])
                break

        if 'expire_date' in api:
            validuntil = float(api['expire_date'])

        if 'traffic_1d' in api:
            traffic     = float(api['traffic_1d'].split(";")[0])
            maxtraffic  = max(maxtraffic, traffic)
            trafficleft = maxtraffic - traffic

        return {'premium': premium, 'validuntil': validuntil, 'trafficleft': trafficleft, 'maxtraffic': maxtraffic}


    def login(self, user, data, req):
        html = self.api_response(user, req)
        err  = re.search(r'**(.+?)**', html)
        if err:
            self.logError(err.group(1))
            self.wrongPassword()
