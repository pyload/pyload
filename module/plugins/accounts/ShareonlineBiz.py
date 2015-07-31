# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Account import Account


class ShareonlineBiz(Account):
    __name__    = "ShareonlineBiz"
    __type__    = "account"
    __version__ = "0.36"
    __status__  = "testing"

    __description__ = """Share-online.biz account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def api_response(self, user, password, req):
        res = self.load("http://api.share-online.biz/cgi-bin",
                        get={'q'       : "userdetails",
                             'aux'     : "traffic",
                             'username': user,
                             'password': password})

        self.log_debug(res)

        api = {}
        for line in res.splitlines():
            if "=" in line:
                key, value = line.split("=")
                api[key] = value

        if not api['a']:
            self.login_fail(_("Invalid username/password"))

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
        err = re.search(r'\*\*(.+?)\*\*', api)

        if not err:
            req.cj.setCookie("share-online.biz", 'a', api['a'])
        else:
            self.login_fail(err.group(1))
