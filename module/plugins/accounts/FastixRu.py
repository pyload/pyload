# -*- coding: utf-8 -*-

from module.plugins.internal.Account import Account
from module.common.json_layer import json_loads


class FastixRu(Account):
    __name__    = "FastixRu"
    __type__    = "account"
    __version__ = "0.07"
    __status__  = "testing"

    __description__ = """Fastix account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Massimo Rosamilia", "max@spiritix.eu")]


    def grab_hosters(self, user, password, data, req):
        html = self.load("http://fastix.ru/api_v2",
                      get={'apikey': "5182964c3f8f9a7f0b00000a_kelmFB4n1IrnCDYuIFn2y",
                           'sub'   : "allowed_sources"})
        host_list = json_loads(html)
        host_list = host_list['allow']
        return host_list


    def grab_info(self, user, password, data, req):
        data = self.get_data(user)
        html = json_loads(self.load("http://fastix.ru/api_v2/",
                                    get={'apikey': data['apikey'],
                                         'sub'   : "getaccountdetails"}))

        points = html['points']
        kb     = float(points) * 1024 ** 2 / 1000

        if points > 0:
            account_info = {'validuntil': -1, 'trafficleft': kb}
        else:
            account_info = {'validuntil': None, 'trafficleft': None, 'premium': False}
        return account_info


    def login(self, user, password, data, req):
        api = json_loads(self.load("https://fastix.ru/api_v2/",
                                   get={'sub'     : "get_apikey",
                                        'email'   : user,
                                        'password': password}))

        if 'error' in api:
            self.fail_login(api['error_txt'])

        else:
            data['apikey'] = api['apikey']
