# -*- coding: utf-8 -*-

import hashlib
import re
import time

from passlib.hash import md5_crypt

from module.plugins.internal.Account import Account


class WebshareCz(Account):
    __name__    = "WebshareCz"
    __type__    = "account"
    __version__ = "0.10"
    __status__  = "testing"

    __description__ = """Webshare.cz account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("rush", "radek.senfeld@gmail.com")]


    VALID_UNTIL_PATTERN = r'<vip_until>(.+)</vip_until>'

    TRAFFIC_LEFT_PATTERN = r'<bytes>(.+)</bytes>'


    def parse_info(self, user, password, data, req):
        html = self.load("https://webshare.cz/api/user_data/",
                        post={'wst': self.get_data(user).get('wst', None)})

        self.log_debug("Response: " + html)

        expiredate = re.search(self.VALID_UNTIL_PATTERN, html).group(1)
        self.log_debug("Expire date: " + expiredate)

        validuntil  = time.mktime(time.strptime(expiredate, "%Y-%m-%d %H:%M:%S"))
        trafficleft = self.parse_traffic(re.search(self.TRAFFIC_LEFT_PATTERN, html).group(1))
        premium     = validuntil > time.time()

        return {'validuntil': validuntil, 'trafficleft': -1, 'premium': premium}


    def login(self, user, password, data, req):
        salt = self.load("https://webshare.cz/api/salt/",
                         post={'username_or_email': user,
                               'wst'              : ""})

        if "<status>OK</status>" not in salt:
            self.login_fail()

        salt     = re.search('<salt>(.+)</salt>', salt).group(1)
        password = hashlib.sha1(md5_crypt.encrypt(password, salt=salt)).hexdigest()
        digest   = hashlib.md5(user + ":Webshare:" + password).hexdigest()

        login = self.load("https://webshare.cz/api/login/",
                          post={'digest'           : digest,
                                'keep_logged_in'   : 1,
                                'password'         : password,
                                'username_or_email': user,
                                'wst'              : ""})

        if "<status>OK</status>" not in login:
            self.login_fail()

        data['wst'] = re.search('<token>(.+)</token>', login).group(1)
