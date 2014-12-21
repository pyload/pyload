# -*- coding: utf-8 -*-

import re

from hashlib import md5, sha1
from passlib.hash import md5_crypt
from urlparse import urljoin
from time import mktime, strptime, time

from module.plugins.Account import Account


class WebshareCz(Account):
    __name__    = "WebshareCz"
    __type__    = "account"
    __version__ = "0.07"

    __description__ = """Webshare.cz account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("rush", "radek.senfeld@gmail.com")]


    TRAFFIC_LEFT_PATTERN = r'<li class="menu-kredit"><a href="/kredit" title="[^"]*?GB = ([\d.]+) MB"'


    def loadAccountInfo(self, user, req):
        info = req.load('https://webshare.cz/api/user_data/',
                        post={"wst": self.wst},
                        decode=True)

        self.logDebug("Response: " + info)

        validuntil = re.search('<vip_until>(.+)</vip_until>', info).group(1)
        validuntil = mktime(strptime(validuntil, "%Y-%m-%d %H:%M:%S"))

        trafficleft = re.search('<bytes>(.+)</bytes>', info).group(1)
        trafficleft = self.parseTraffic(trafficleft)

        premium = validuntil > time()

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}


    def login(self, user, data, req):
        salt = req.load('https://webshare.cz/api/salt/',
                        post={"username_or_email": user,
                              "wst": ""},
                        decode=True)

        self.logDebug("Response: " + salt)

        if "<status>OK</status>" not in salt:
            self.wrongPassword()

        salt = re.search('<salt>(.+)</salt>', salt).group(1)
        password = sha1(md5_crypt.encrypt(data["password"], salt=salt)).hexdigest()
        digest = md5(user + ":Webshare:" + password).hexdigest()

        login = req.load('https://webshare.cz/api/login/',
                        post={"digest": digest,
                              "keep_logged_in": 1,
                              "password": password,
                              "username_or_email": user,
                              "wst": ""},
                        decode=True)

        self.logDebug("Response: " + login)

        if "<status>OK</status>" not in login:
            self.wrongPassword()

        self.wst = re.search('<token>(.+)</token>', login).group(1)
