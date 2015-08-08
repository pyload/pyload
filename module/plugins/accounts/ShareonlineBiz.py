# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Account import Account
from module.plugins.internal.Plugin import set_cookie


class ShareonlineBiz(Account):
    __name__    = "ShareonlineBiz"
    __type__    = "account"
    __version__ = "0.39"
    __status__  = "testing"

    __description__ = """Share-online.biz account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def api_response(self, user, password, req):
        res = self.load("https://api.share-online.biz/cgi-bin",
                        get={'q'       : "userdetails",
                             'aux'     : "traffic",
                             'username': user,
                             'password': password},
                        decode=False)

        self.log_debug(res)

        api = dict(line.split("=") for line in res.splitlines() if "=" in line)

        if not 'a' in api:
            self.login_fail(res.strip('*').strip())

        if api['a'].lower() == "not_available":
            self.login_fail(_("No info available"))

        return api


    def parse_info(self, user, password, data, req):
        premium     = False
        validuntil  = None
        trafficleft = -1
        maxtraffic  = 100 * 1024 * 1024 * 1024  #: 100 GB

        api = self.api_response(user, password, req)

        premium    = api['group'] in ("PrePaid", "Premium", "Penalty-Premium")
        validuntil = float(api['expire_date'])
        traffic    = float(api['traffic_1d'].split(";")[0])

        if maxtraffic > traffic:
            trafficleft = maxtraffic - traffic
        else:
            trafficleft = -1

        maxtraffic  /= 1024  #@TODO: Remove `/ 1024` in 0.4.10
        trafficleft /= 1024  #@TODO: Remove `/ 1024` in 0.4.10

        return {'premium'    : premium,
                'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'maxtraffic' : maxtraffic}


    def login(self, user, password, data, req):
        api = self.api_response(user, password, req)
        set_cookie(req.cj, "share-online.biz", 'a', api['a'])
