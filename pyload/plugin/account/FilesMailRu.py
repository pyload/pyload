# -*- coding: utf-8 -*-

from pyload.plugin.Account import Account


class FilesMailRu(Account):
    __name    = "FilesMailRu"
    __type    = "account"
    __version = "0.11"

    __description = """Filesmail.ru account plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org")]


    def loadAccountInfo(self, user, req):
        return {"validuntil": None, "trafficleft": None}


    def login(self, user, data, req):
        user, domain = user.split("@")

        html = req.load("http://swa.mail.ru/cgi-bin/auth",
                        post={"Domain": domain,
                              "Login": user,
                              "Password": data['password'],
                              "Page": "http://files.mail.ru/"},
                        decode=True)

        if "Неверное имя пользователя или пароль" in html:
            self.wrongPassword()
