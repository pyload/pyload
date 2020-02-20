# -*- coding: utf-8 -*-

import time

from ..internal.Account import Account
from ..internal.misc import json


class FilejokerNet(Account):
    __name__ = "FilejokerNet"
    __type__ = "account"
    __version__ = "0.04"
    __status__ = "testing"

    __description__ = """Filejoker.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://filejoker.net/zapi"


    def api_response(self, op, **kwargs):
        args = {'op': op}
        args.update(kwargs)
        return json.loads(self.load(self.API_URL, get=args))

    def grab_info(self, user, password, data):
        res = self.api_response("my_account", session=data['session'])
        premium_expire = res.get('usr_premium_expire')

        validuntil = time.mktime(time.strptime(premium_expire, "%Y-%m-%d %H:%M:%S")) if premium_expire else -1
        trafficleft = int(res['traffic_left']) * 1024 ** 2 if 'traffic_left' in res else None
        premium = bool(premium_expire)

        return {'validuntil': validuntil,
                'trafficleft': trafficleft,
                'premium': premium}


    def signin(self, user, password, data):
        session = data.get('session')
        if session and 'error' not in self.api_response("my_account", session=session):
            self.skip_login()

        res = self.api_response("login", **{'email': user, 'pass': password})
        if 'error'in res:
            self.fail_login()

        data['session'] = res['session']
