# -*- coding: utf-8 -*-

import re
from module.plugins.Account import Account

class ShareRapidCom(Account):
    __name__ = "ShareRapidCom"
    __version__ = "0.31"
    __type__ = "account"
    __description__ = """ShareRapid account plugin"""
    __author_name__ = ("MikyWoW")

    def loadAccountInfo(self, user, req):
        src = req.load("http://share-rapid.com/mujucet/", cookies=True)
        found = re.search(r'<tr><td>GB:</td><td>(.*?) GB', src)
        if found:
            ret = float(found.group(1)) * (1 << 20)
            tmp = {"premium": True, "trafficleft": ret, "validuntil": -1}
        else:
            tmp = {"premium": False, "trafficleft": None, "validuntil": None}
        return tmp

    def login(self, user, data, req):
        htm = req.load("http://share-rapid.com/prihlaseni/", cookies=True)
        if "Heslo:" in htm:
            start = htm.index('id="inp_hash" name="hash" value="')
            htm = htm[start+33:]
            hashes = htm[0:32]
            htm = req.load("http://share-rapid.com/prihlaseni/",
                post={"hash": hashes,"login": user, "pass1": data["password"],"remember": 0,
                      "sbmt": "P%C5%99ihl%C3%A1sit"}, cookies=True)
            
            #if "Heslo:" in htm:
            #    self.wrongPassword()