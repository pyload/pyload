# -*- coding: utf-8 -*-

from time import mktime, strptime
import re

from module.plugins.Account import Account


class CzshareCom(Account):
    __name__ = "CzshareCom"
    __type__ = "account"
    __version__ = "0.14"

    __description__ = """Czshare.com account plugin, now Sdilej.cz"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    CREDIT_LEFT_PATTERN = r'<tr class="active">\s*<td>([0-9 ,]+) (KiB|MiB|GiB)</td>\s*<td>([^<]*)</td>\s*</tr>'


    def loadAccountInfo(self, user, req):
        html = req.load("http://sdilej.cz/prehled_kreditu/")

        m = re.search(self.CREDIT_LEFT_PATTERN, html)
        if m is None:
            return {"validuntil": 0, "trafficleft": 0}
        else:
            credits = float(m.group(1).replace(' ', '').replace(',', '.'))
            credits = credits * 1024 ** {'KiB': 0, 'MiB': 1, 'GiB': 2}[m.group(2)]
            validuntil = mktime(strptime(m.group(3), '%d.%m.%y %H:%M'))
            return {"validuntil": validuntil, "trafficleft": credits}

    def login(self, user, data, req):
        html = req.load('https://sdilej.cz/index.php', post={
            "Prihlasit": "Prihlasit",
            "login-password": data['password'],
            "login-name": user
        })

        if '<div class="login' in html:
            self.wrongPassword()
