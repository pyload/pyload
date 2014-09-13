# -*- coding: utf-8 -*-

from time import mktime, strptime

from module.plugins.Account import Account


class ZeveraCom(Account):
    __name__ = "ZeveraCom"
    __type__ = "account"
    __version__ = "0.21"

    __description__ = """Zevera.com account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


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

        response = req.load("http://www.zevera.com/jDownloader.ashx", get=get_data,
                            decode=True, just_header=just_header)
        self.logDebug(response)

        if ':' in response:
            if not just_header:
                response = response.replace(',', '\n')
            return dict((y.strip().lower(), z.strip()) for (y, z) in
                        [x.split(':', 1) for x in response.splitlines() if ':' in x])
        else:
            return response
