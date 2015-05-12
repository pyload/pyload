# -*- coding: utf-8 -*-

import hashlib
import passlib
import re
import time

from pyload.plugin.Account import Account


class WebshareCz(Account):
    __name    = "WebshareCz"
    __type    = "account"
    __version = "0.07"

    __description = """Webshare.cz account plugin"""
    __license     = "GPLv3"
    __authors     = [("rush", "radek.senfeld@gmail.com")]


    VALID_UNTIL_PATTERN = r'<vip_until>(.+)</vip_until>'

    TRAFFIC_LEFT_PATTERN = r'<bytes>(.+)</bytes>'


    def loadAccountInfo(self, user, req):
        html = req.load("https://webshare.cz/api/user_data/",
                        post={'wst': self.infos['wst']},
                        decode=True)

        self.logDebug("Response: " + html)

        expiredate = re.search(self.VALID_UNTIL_PATTERN, html).group(1)
        self.logDebug("Expire date: " + expiredate)

        validuntil  = time.mktime(time.strptime(expiredate, "%Y-%m-%d %H:%M:%S"))
        trafficleft = self.parseTraffic(re.search(self.TRAFFIC_LEFT_PATTERN, html).group(1))
        premium     = validuntil > time.time()

        return {'validuntil': validuntil, 'trafficleft': -1, 'premium': premium}


    def login(self, user, data, req):
        salt = req.load("https://webshare.cz/api/salt/",
                        post={'username_or_email': user,
                              'wst'              : ""},
                        decode=True)

        if "<status>OK</status>" not in salt:
            self.wrongPassword()

        salt     = re.search('<salt>(.+)</salt>', salt).group(1)
        password = hashlib.sha1(passlib.hash.md5_crypt.encrypt(data['password'], salt=salt)).hexdigest()
        digest   = hashlib.md5(user + ":Webshare:" + password).hexdigest()

        login = req.load("https://webshare.cz/api/login/",
                         post={'digest'           : digest,
                               'keep_logged_in'   : 1,
                               'password'         : password,
                               'username_or_email': user,
                               'wst'              : ""},
                         decode=True)

        if "<status>OK</status>" not in login:
            self.wrongPassword()

        self.infos['wst'] = re.search('<token>(.+)</token>', login).group(1)
