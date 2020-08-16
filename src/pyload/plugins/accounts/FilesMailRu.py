# -*- coding: utf-8 -*-

from ..base.account import BaseAccount


class FilesMailRu(BaseAccount):
    __name__ = "FilesMailRu"
    __type__ = "account"
    __version__ = "0.18"
    __status__ = "testing"

    __description__ = """Filesmail.ru account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.net")]

    def grab_info(self, user, password, data):
        return {"validuntil": None, "trafficleft": None}

    def signin(self, user, password, data):
        user, domain = user.split("@")

        html = self.load(
            "https://swa.mail.ru/cgi-bin/auth",
            post={
                "Domain": domain,
                "Login": user,
                "Password": password,
                "Page": "http://files.mail.ru/",
            },
        )

        if "Неверное имя пользователя или пароль" in html:
            self.fail_login()
