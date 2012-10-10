# -*- coding: utf-8 -*-

import re
from time import mktime, strptime
from module.plugins.Account import Account

class ShareRapidCom(Account):
    __name__ = "ShareRapidCom"
    __version__ = "0.32"
    __type__ = "account"
    __description__ = """ShareRapid account plugin"""
    __author_name__ = ("MikyWoW", "zoidberg")
    
    login_timeout = 60
        
    def loadAccountInfo(self, user, req):
        src = req.load("http://share-rapid.com/mujucet/", decode=True)
        
        found = re.search(ur'<td>Max. počet paralelních stahování: </td><td>(\d+)', src)
        if found:
            data = self.getAccountData(user)
            data["options"]["limitDL"] = [int(found.group(1))]
        
        found = re.search(ur'<td>Paušální stahování aktivní. Vyprší </td><td><strong>(.*?)</strong>', src)
        if found:
            validuntil = mktime(strptime(found.group(1), "%d.%m.%Y - %H:%M"))
            return {"premium": True, "trafficleft": -1, "validuntil": validuntil}        
        
        found = re.search(r'<tr><td>GB:</td><td>(.*?) GB', src)
        if found:
            trafficleft = float(found.group(1)) * (1 << 20)
            return {"premium": True, "trafficleft": trafficleft, "validuntil": -1}
        
        return {"premium": False, "trafficleft": None, "validuntil": None}

    def login(self, user, data, req):
        htm = req.load("http://share-rapid.com/prihlaseni/", cookies=True)
        if "Heslo:" in htm:
            start = htm.index('id="inp_hash" name="hash" value="')
            htm = htm[start+33:]
            hashes = htm[0:32]
            htm = req.load("http://share-rapid.com/prihlaseni/",
                           post={"hash": hashes,
                                 "login": user, 
                                 "pass1": data["password"],
                                 "remember": 0,
                                 "sbmt": u"Přihlásit"}, cookies=True)