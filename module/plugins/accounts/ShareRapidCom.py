# -*- coding: utf-8 -*-

import re

from time import mktime, strptime
from module.plugins.Account import Account


class ShareRapidCom(Account):
    __name__ = "ShareRapidCom"
    __type__ = "account"
    __version__ = "0.34"

    __description__ = """MegaRapid.cz account plugin"""
    __author_name__ = ("MikyWoW", "zoidberg")
    __author_mail__ = ("mikywow@seznam.cz", "zoidberg@mujmail.cz")

    login_timeout = 60


    def loadAccountInfo(self, user, req):
        src = req.load("http://megarapid.cz/mujucet/", decode=True)

        m = re.search(ur'<td>Max. počet paralelních stahování: </td><td>(\d+)', src)
        if m:
            data = self.getAccountData(user)
            data['options']['limitDL'] = [int(m.group(1))]

        m = re.search(ur'<td>Paušální stahování aktivní. Vyprší </td><td><strong>(.*?)</strong>', src)
        if m:
            validuntil = mktime(strptime(m.group(1), "%d.%m.%Y - %H:%M"))
            return {"premium": True, "trafficleft": -1, "validuntil": validuntil}

        m = re.search(r'<tr><td>Kredit</td><td>(.*?) GiB', src)
        if m:
            trafficleft = float(m.group(1)) * (1 << 20)
            return {"premium": True, "trafficleft": trafficleft, "validuntil": -1}

        return {"premium": False, "trafficleft": None, "validuntil": None}

    def login(self, user, data, req):
        htm = req.load("http://megarapid.cz/prihlaseni/", cookies=True)
        if "Heslo:" in htm:
            start = htm.index('id="inp_hash" name="hash" value="')
            htm = htm[start + 33:]
            hashes = htm[0:32]
            htm = req.load("http://megarapid.cz/prihlaseni/",
                           post={"hash": hashes,
                                 "login": user,
                                 "pass1": data['password'],
                                 "remember": 0,
                                 "sbmt": u"Přihlásit"}, cookies=True)
