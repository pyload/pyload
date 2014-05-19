# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: zoidberg
"""

from time import mktime, strptime
import re

from module.plugins.Account import Account


class CzshareCom(Account):
    __name__ = "CzshareCom"
    __version__ = "0.14"
    __type__ = "account"
    __description__ = """Czshare.com account plugin, now Sdilej.cz"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")

    CREDIT_LEFT_PATTERN = r'<tr class="active">\s*<td>([0-9 ,]+) (KiB|MiB|GiB)</td>\s*<td>([^<]*)</td>\s*</tr>'

    def loadAccountInfo(self, user, req):
        html = req.load("http://sdilej.cz/prehled_kreditu/")

        found = re.search(self.CREDIT_LEFT_PATTERN, html)
        if not found:
            return {"validuntil": 0, "trafficleft": 0}
        else:
            credits = float(found.group(1).replace(' ', '').replace(',', '.'))
            credits = credits * 1024 ** {'KiB': 0, 'MiB': 1, 'GiB': 2}[found.group(2)]
            validuntil = mktime(strptime(found.group(3), '%d.%m.%y %H:%M'))
            return {"validuntil": validuntil, "trafficleft": credits}

    def login(self, user, data, req):
        html = req.load('https://sdilej.cz/index.php', post={
            "Prihlasit": "Prihlasit",
            "login-password": data["password"],
            "login-name": user
        })

        if '<div class="login' in html:
            self.wrongPassword()
