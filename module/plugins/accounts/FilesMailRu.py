# -*- coding: utf-8 -*-

from module.plugins.Account import Account


class FilesMailRu(Account):
    __name__ = "FilesMailRu"
    __type__ = "account"
    __version__ = "0.1"

    __description__ = """Filesmail.ru account plugin"""
    __author_name__ = "RaNaN"
    __author_mail__ = "RaNaN@pyload.org"


    def loadAccountInfo(self, user, req):
        return {"validuntil": None, "trafficleft": None}

    def login(self, user, data, req):
        user, domain = user.split("@")

        page = req.load("http://swa.mail.ru/cgi-bin/auth", None,
                        {"Domain": domain, "Login": user, "Password": data['password'],
                         "Page": "http://files.mail.ru/"}, cookies=True)

        if "Неверное имя пользователя или пароль" in page:  # @TODO seems not to work
            self.wrongPassword()
