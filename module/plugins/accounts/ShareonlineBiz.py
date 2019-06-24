# -*- coding: utf-8 -*-


from ..internal.Account import Account
from ..internal.misc import set_cookie


class ShareonlineBiz(Account):
    __name__ = "ShareonlineBiz"
    __type__ = "account"
    __version__ = "0.47"
    __status__ = "testing"

    __description__ = """Share-online.biz account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def api_response(self, user, password):
        res = self.load("https://api.share-online.biz/cgi-bin",
                        get={'q': "userdetails",
                             'aux': "traffic",
                             'username': user,
                             'password': password},
                        decode=False)

        api = dict(line.split("=", 1) for line in res.splitlines() if "=" in line) or \
            {'error': res.strip('* ')}

        return api

    def grab_info(self, user, password, data):
        premium = False
        validuntil = None
        trafficleft = -1
        maxtraffic = 100 * 1024 * 1024 * 1024  #: 100 GB

        api_info = self.api_response(user, password)

        premium = api_info['group'] in ("PrePaid", "Premium", "Penalty-Premium", "VIP", "VIP-Special")
        validuntil = float(api_info['expire_date'])
        traffic = float(api_info['traffic_1d'].split(";")[0])

        if maxtraffic > traffic:
            trafficleft = maxtraffic - traffic

        else:
            trafficleft = -1

        trafficleft /= 1024  # @TODO: Remove `/ 1024` in 0.4.10

        return {'premium': premium,
                'validuntil': validuntil,
                'trafficleft': trafficleft}

    def signin(self, user, password, data):
        api_info = self.api_response(user, password)

        if 'a' not in api_info:
            self.fail_login(api_info['error'])

        else:
            set_cookie(self.req.cj, "share-online.biz", 'a', api_info['a'])
