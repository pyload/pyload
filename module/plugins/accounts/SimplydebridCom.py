# -*- coding: utf-8 -*-

import time

from module.plugins.internal.Account import Account


class SimplydebridCom(Account):
    __name__    = "SimplydebridCom"
    __type__    = "account"
    __version__ = "0.13"
    __status__  = "testing"

    __description__ = """Simply-Debrid.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Kagenoshin", "kagenoshin@gmx.ch")]


    def parse_info(self, user, password, data, req):
        res = self.load("http://simply-debrid.com/api.php",
                        get={'login': 2,
                             'u'    : user,
                             'p'    : password})
        data = [x.strip() for x in res.split(";")]
        if str(data[0]) != "1":
            return {'premium': False}
        else:
            return {'trafficleft': -1, 'validuntil': time.mktime(time.strptime(str(data[2]), "%d/%m/%Y"))}


    def login(self, user, password, data, req):
        res = self.load("https://simply-debrid.com/api.php",
                        get={'login': 1,
                             'u'    : user,
                             'p'    : password})
        if res != "02: loggin success":
            self.login_fail()
