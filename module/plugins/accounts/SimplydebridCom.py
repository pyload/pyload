# -*- coding: utf-8 -*-

from time import mktime, strptime

from module.plugins.Account import Account


class SimplydebridCom(Account):
    __name__ = "SimplydebridCom"
    __type__ = "account"
    __version__ = "0.1"

    __description__ = """Simply-Debrid.com account plugin"""
    __author_name__ = "Kagenoshin"
    __author_mail__ = "kagenoshin@gmx.ch"


    def loadAccountInfo(self, user, req):
        get_data = {'login': 2, 'u': self.loginname, 'p': self.password}
        response = req.load("http://simply-debrid.com/api.php", get=get_data, decode=True)
        data = [x.strip() for x in response.split(";")]
        if str(data[0]) != "1":
            return {"premium": False}
        else:
            return {"trafficleft": -1, "validuntil": mktime(strptime(str(data[2]), "%d/%m/%Y"))}

    def login(self, user, data, req):
        self.loginname = user
        self.password = data['password']
        get_data = {'login': 1, 'u': self.loginname, 'p': self.password}
        response = req.load("http://simply-debrid.com/api.php", get=get_data, decode=True)
        if response != "02: loggin success":
            self.wrongPassword()
