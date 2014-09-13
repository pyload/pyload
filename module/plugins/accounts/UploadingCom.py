# -*- coding: utf-8 -*-

from time import time, strptime, mktime
import re

from module.plugins.Account import Account


class UploadingCom(Account):
    __name__ = "UploadingCom"
    __type__ = "account"
    __version__ = "0.1"

    __description__ = """Uploading.com account plugin"""
    __author_name__ = "mkaay"
    __author_mail__ = "mkaay@mkaay.de"


    def loadAccountInfo(self, user, req):
        src = req.load("http://uploading.com/")
        premium = True
        if "UPGRADE TO PREMIUM" in src:
            return {"validuntil": -1, "trafficleft": -1, "premium": False}

        m = re.search("Valid Until:(.*?)<", src)
        if m:
            validuntil = int(mktime(strptime(m.group(1).strip(), "%b %d, %Y")))
        else:
            validuntil = -1

        return {"validuntil": validuntil, "trafficleft": -1, "premium": True}

    def login(self, user, data, req):
        req.cj.setCookie("uploading.com", "lang", "1")
        req.cj.setCookie("uploading.com", "language", "1")
        req.cj.setCookie("uploading.com", "setlang", "en")
        req.cj.setCookie("uploading.com", "_lang", "en")
        req.load("http://uploading.com/")
        req.load("http://uploading.com/general/login_form/?JsHttpRequest=%s-xml" % long(time() * 1000),
                 post={"email": user, "password": data['password'], "remember": "on"})
