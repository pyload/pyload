# -*- coding: utf-8 -*-

import re
import time

import pycurl
from module.network.HTTPRequest import BadHeader

from ..internal.Account import Account


class OneFichierCom(Account):
    __name__ = "OneFichierCom"
    __type__ = "account"
    __version__ = "0.24"
    __status__ = "testing"

    __description__ = """1fichier.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Elrick69", "elrick69[AT]rocketmail[DOT]com"),
                   ("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    VALID_UNTIL_PATTERN = r'valid until <span style="font-weight:bold">(\d+\-\d+\-\d+)<'

    def grab_info(self, user, password, data):
        validuntil = None
        trafficleft = -1
        premium = False

        html = self.load("https://1fichier.com/console/abo.pl")

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            expiredate = m.group(1)
            self.log_debug("Expire date: " + expiredate)

            try:
                validuntil = time.mktime(time.strptime(expiredate, "%Y-%m-%d"))

            except Exception, e:
                self.log_error(e, trace=True)

            else:
                premium = True

        return {'validuntil': validuntil,
                'trafficleft': trafficleft,
                'premium': premium}

    def signin(self, user, password, data):
        login_url = "https://1fichier.com/login.pl?lg=en"

        try:
            html = self.load(login_url,
                             ref=login_url,
                             post={'mail': user,
                                   'pass': password,
                                   'It': "on",
                                   'purge': "off",
                                   'valider': "Send"})

            if any(_x in html for _x in
                   ('>Invalid username or Password', '>Invalid email address', '>Invalid password')):
                self.fail_login()

        except BadHeader, e:
            if e.code == 403:
                self.fail_login()
            else:
                raise
