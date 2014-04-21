# -*- coding: utf-8 -*-
import re
from time import mktime, strptime

from module.plugins.Account import Account


class Vipleech4uCom(Account):
    __name__ = "Vipleech4uCom"
    __version__ = "0.1"
    __type__ = "account"
    __description__ = """Vipleech4u.com account plugin"""
    __author_name__ = ("Kagenoshin")
    __author_mail__ = ("kagenoshin@gmx.ch")

    STATUS_PATTERN = re.compile(r'status.*?<\s*?strong\s*?>[^<]*?vip[^<]*?<', re.I)
    VALIDUNTIL_PATTERN = re.compile(r'valid\s*?until.*?<\s*?strong\s*?>([^<]*?)<', re.I)

    def loadAccountInfo(self, user, req):
        response = req.load("http://vipleech4u.com", decode=True)
        status = self.STATUS_PATTERN.search(response)

        validuntil = self.VALIDUNTIL_PATTERN.search(response)
        if validuntil:
            validuntil = validuntil.group(1)

        if status and validuntil:
            print status
            print validuntil
            return {"trafficleft": -1, "validuntil": mktime(strptime("%s 23:59" % validuntil, "%d-%m-%Y %H:%M"))}
        else:
            return {"premium": False}

    def login(self, user, data, req):
        self.loginname = user
        self.password = data["password"]
        post_data = {'action': 'login', 'user': self.loginname, 'pass': self.password}
        req.load("http://vipleech4u.com/login.php")
        response = req.load("http://vipleech4u.com/login.php", post=post_data, decode=True)
        if 'Username or Password are incorrect' in response:
            self.wrongPassword()
