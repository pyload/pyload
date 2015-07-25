# -*- coding: utf-8 -*-

import time

from module.plugins.internal.Account import Account
from module.common.json_layer import json_loads


class FileserveCom(Account):
    __name__    = "FileserveCom"
    __type__    = "account"
    __version__ = "0.22"
    __status__  = "testing"

    __description__ = """Fileserve.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]


    def parse_info(self, user, password, data, req):
        data = self.get_data(user)

        html = self.load("http://app.fileserve.com/api/login/",
                         post={'username': user,
                               'password': password,
                               'submit': "Submit+Query"})
        res = json_loads(html)

        if res['type'] == "premium":
            validuntil = time.mktime(time.strptime(res['expireTime'], "%Y-%m-%d %H:%M:%S"))
            return {'trafficleft': res['traffic'], 'validuntil': validuntil}
        else:
            return {'premium': False, 'trafficleft': None, 'validuntil': None}


    def login(self, user, password, data, req):
        html = self.load("http://app.fileserve.com/api/login/",
                         post={'username': user,
                               'password': password,
                               'submit'  : "Submit+Query"})
        res = json_loads(html)

        if not res['type']:
            self.login_fail()

        #: Login at fileserv html
        self.load("http://www.fileserve.com/login.php",
                  post={'loginUserName'    : user,
                        'loginUserPassword': password,
                        'autoLogin'        : "checked",
                        'loginFormSubmit'  : "Login"})
