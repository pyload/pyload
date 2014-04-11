# -*- coding: utf-8 -*-

from time import mktime, strptime

from pyload.plugins.MultiHoster import MultiHoster


class SimplydebridCom(MultiHoster):
    __name__ = "SimplydebridCom"
    __version__ = "0.1"
    __type__ = "account"
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
        self.password = data["password"]
        get_data = {'login': 1, 'u': self.loginname, 'p': self.password}
        response = req.load("http://simply-debrid.com/api.php", get=get_data, decode=True)
        if response != "02: loggin success":
            self.wrongPassword()

    def loadHosterList(self, req):
        page = req.load("http://simply-debrid.com/api.php?list=1")
        return [x.strip() for x in page.rstrip(';').replace("\"", "").split(";")]
