# -*- coding: utf-8 -*-

import re
import time

from ..base.account import BaseAccount


class MegaRapidCz(BaseAccount):
    __name__ = "MegaRapidCz"
    __type__ = "account"
    __version__ = "0.42"
    __status__ = "testing"

    __description__ = """MegaRapid.cz account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("MikyWoW", "mikywow@seznam.cz"),
        ("zoidberg", "zoidberg@mujmail.cz"),
    ]

    login_timeout = 60

    LIMITDL_PATTERN = r"<td>Max. počet paralelních stahování: </td><td>(\d+)"
    VALID_UNTIL_PATTERN = (
        r"<td>Paušální stahování aktivní. Vyprší </td><td><strong>(.*?)</strong>"
    )
    TRAFFIC_LEFT_PATTERN = r"<tr><td>Kredit</td><td>(.*?) GiB"

    def grab_info(self, user, password, data):
        htmll = self.load("http://megarapid.cz/mujucet/")

        m = re.search(self.LIMITDL_PATTERN, htmll)
        if m is not None:
            data["options"]["limit_dl"] = [int(m.group(1))]

        m = re.search(self.VALID_UNTIL_PATTERN, htmll)
        if m is not None:
            validuntil = time.mktime(time.strptime(m.group(1), "%d.%m.%Y - %H:%M"))
            return {"premium": True, "trafficleft": -1, "validuntil": validuntil}

        m = re.search(self.TRAFFIC_LEFT_PATTERN, htmll)
        if m is not None:
            trafficleft = float(m.group(1)) * (1 << 20)
            return {"premium": True, "trafficleft": trafficleft, "validuntil": -1}

        return {"premium": False, "trafficleft": None, "validuntil": None}

    def signin(self, user, password, data):
        html = self.load("http://megarapid.cz/prihlaseni/")

        if "Heslo:" in html:
            start = html.index('id="inp_hash" name="hash" value="')
            html = html[start + 33 :]
            hashes = html[0:32]
            html = self.load(
                "https://megarapid.cz/prihlaseni/",
                post={
                    "hash": hashes,
                    "login": user,
                    "pass1": password,
                    "remember": 1,
                    "sbmt": "Přihlásit",
                },
            )
