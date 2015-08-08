# -*- coding: utf-8 -*-

from module.plugins.internal.Account import Account


class FilesMailRu(Account):
    __name__    = "FilesMailRu"
    __type__    = "account"
    __version__ = "0.13"
    __status__  = "testing"

    __description__ = """Filesmail.ru account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def parse_info(self, user, password, data, req):
        return {'validuntil': None, 'trafficleft': None}


    def login(self, user, password, data, req):
        user, domain = user.split("@")

        html = self.load("https://swa.mail.ru/cgi-bin/auth",
                         post={'Domain'  : domain,
                               'Login'   : user,
                               'Password': password,
                               'Page'    : "http://files.mail.ru/"})

        if "Неверное имя пользователя или пароль" in html:
            self.login_fail()
