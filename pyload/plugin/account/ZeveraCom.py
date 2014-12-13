# -*- coding: utf-8 -*-

from time import mktime, strptime

from pyload.plugin.Account import Account


class ZeveraCom(Account):
    __name    = "ZeveraCom"
    __type    = "account"
    __version = "0.21"

    __description = """Zevera.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    def loadAccountInfo(self, user, req):
        data = self.getAPIData(req)
        if data == "No traffic":
            account_info = {"trafficleft": 0, "validuntil": 0, "premium": False}
        else:
            account_info = {
                "trafficleft": int(data['availabletodaytraffic']) * 1024,
                "validuntil": mktime(strptime(data['endsubscriptiondate'], "%Y/%m/%d %H:%M:%S")),
                "premium": True
            }
        return account_info


    def login(self, user, data, req):
        self.loginname = user
        self.password = data['password']
        if self.getAPIData(req) == "No traffic":
            self.wrongPassword()


    def getAPIData(self, req, just_header=False, **kwargs):
        get_data = {
            'cmd': 'accountinfo',
            'login': self.loginname,
            'pass': self.password
        }
        get_data.update(kwargs)

        res = req.load("http://www.zevera.com/jDownloader.ashx", get=get_data,
                            decode=True, just_header=just_header)
        self.logDebug(res)

        if ':' in res:
            if not just_header:
                res = res.replace(',', '\n')
            return dict((y.strip().lower(), z.strip()) for (y, z) in
                        [x.split(':', 1) for x in res.splitlines() if ':' in x])
        else:
            return res
