# -*- coding: utf-8 -*-

from module.plugins.Account import Account


class FilesMailRu(Account):
    __name__    = "FilesMailRu"
    __type__    = "account"
    __version__ = "0.11"

    __description__ = """Filesmail.ru account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def loadAccountInfo(self, user, req):
        return {"validuntil": None, "trafficleft": None}


    def login(self, user, data, req):
        user, domain = user.split("@")

        html = req.load("http://swa.mail.ru/cgi-bin/auth",
                        post={"Domain": domain,
                              "Login": user,
                              "Password": data['password'],
                              "Page": "http://files.mail.ru/"},
                        cookies=True,
                        decode=True)

        if "Неверное имя пользователя или пароль" in html:
            self.wrongPassword()
