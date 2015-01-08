# -*- coding: utf-8 -*-

from time import mktime, strptime

from module.plugins.Account import Account


class ZeveraCom(Account):
    __name__    = "ZeveraCom"
    __type__    = "account"
    __version__ = "0.23"

    __description__ = """Zevera.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    API_URL = "http://api.zevera.com/jDownloader.ashx"


    def loadAccountInfo(self, user, req):
        validuntil  = None
        trafficleft = None
        premium     = False

        api = self.api_response(req)

        if api != "No trafic":
            validuntil  = mktime(strptime(api['endsubscriptiondate'], "%Y/%m/%d %H:%M:%S"))
            trafficleft = float(api['availabletodaytraffic']) * 1024 if api['orondaytrafficlimit'] != '0' else -1
            premium     = True

        return {'validuntil': validuntil, 'trafficleft': trafficleft, 'premium': premium}


    def login(self, user, data, req):
        self.user     = user
        self.password = data['password']

        if self.api_response(req) == "No trafic":
            self.wrongPassword()


    def api_response(self, req, just_header=False, **kwargs):
        get_data = {'cmd'  : "accountinfo",
                    'login': self.user,
                    'pass' : self.password}

        get_data.update(kwargs)

        res = req.load(self.API_URL,
                       get=get_data,
                       just_header=just_header,
                       decode=True)

        self.logDebug(res)

        if ':' in res:
            if not just_header:
                res = res.replace(',', '\n')
            return dict((y.strip().lower(), z.strip()) for (y, z) in
                        [x.split(':', 1) for x in res.splitlines() if ':' in x])
        else:
            return res
