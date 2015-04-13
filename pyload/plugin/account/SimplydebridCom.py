# -*- coding: utf-8 -*-

import time

from pyload.plugin.Account import Account


class SimplydebridCom(Account):
    __name    = "SimplydebridCom"
    __type    = "account"
    __version = "0.11"

    __description = """Simply-Debrid.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Kagenoshin", "kagenoshin@gmx.ch")]


    def loadAccountInfo(self, user, req):
        get_data = {'login': 2, 'u': self.loginname, 'p': self.password}
        res = req.load("http://simply-debrid.com/api.php", get=get_data, decode=True)
        data = [x.strip() for x in res.split(";")]
        if str(data[0]) != "1":
            return {"premium": False}
        else:
            return {"trafficleft": -1, "validuntil": time.mktime(time.strptime(str(data[2]), "%d/%m/%Y"))}


    def login(self, user, data, req):
        self.loginname = user
        self.password  = data['password']
        get_data       = {'login': 1, 'u': self.loginname, 'p': self.password}

        res = req.load("http://simply-debrid.com/api.php", get=get_data, decode=True)
        if res != "02: loggin success":
            self.wrongPassword()
