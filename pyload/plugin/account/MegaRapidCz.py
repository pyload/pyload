# -*- coding: utf-8 -*-

import re

from time import mktime, strptime
from pyload.plugin.Account import Account


class MegaRapidCz(Account):
    __name    = "MegaRapidCz"
    __type    = "account"
    __version = "0.34"

    __description = """MegaRapid.cz account plugin"""
    __license     = "GPLv3"
    __authors     = [("MikyWoW", "mikywow@seznam.cz"),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    login_timeout = 60

    LIMITDL_PATTERN = ur'<td>Max. počet paralelních stahování: </td><td>(\d+)'
    VALID_UNTIL_PATTERN = ur'<td>Paušální stahování aktivní. Vyprší </td><td><strong>(.*?)</strong>'
    TRAFFIC_LEFT_PATTERN = r'<tr><td>Kredit</td><td>(.*?) GiB'


    def loadAccountInfo(self, user, req):
        html = req.load("http://megarapid.cz/mujucet/", decode=True)

        m = re.search(self.LIMITDL_PATTERN, html)
        if m:
            data = self.getAccountData(user)
            data['options']['limitDL'] = [int(m.group(1))]

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            validuntil = mktime(strptime(m.group(1), "%d.%m.%Y - %H:%M"))
            return {"premium": True, "trafficleft": -1, "validuntil": validuntil}

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            trafficleft = float(m.group(1)) * (1 << 20)
            return {"premium": True, "trafficleft": trafficleft, "validuntil": -1}

        return {"premium": False, "trafficleft": None, "validuntil": None}


    def login(self, user, data, req):
        htm = req.load("http://megarapid.cz/prihlaseni/")
        if "Heslo:" in htm:
            start = htm.index('id="inp_hash" name="hash" value="')
            htm = htm[start + 33:]
            hashes = htm[0:32]
            htm = req.load("http://megarapid.cz/prihlaseni/",
                           post={"hash": hashes,
                                 "login": user,
                                 "pass1": data['password'],
                                 "remember": 0,
                                 "sbmt": u"Přihlásit"})
