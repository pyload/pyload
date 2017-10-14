# -*- coding: utf-8 -*-

import re
import time

from ..internal.Account import Account


class NowVideoSx(Account):
    __name__ = "NowVideoSx"
    __type__ = "account"
    __version__ = "0.11"
    __status__ = "testing"

    __description__ = """NowVideo.at account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    VALID_UNTIL_PATTERN = r'>Your premium membership expires on: (.+?)<'

    def grab_info(self, user, password, data):
        validuntil = None
        trafficleft = -1
        premium = None

        html = self.load("http://www.nowvideo.sx/premium.php")

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            expiredate = m.group(1).strip()
            self.log_debug("Expire date: " + expiredate)

            try:
                validuntil = time.mktime(time.strptime(expiredate, "%Y-%b-%d"))

            except Exception, e:
                self.log_error(e, trace=True)

            else:
                if validuntil > time.mktime(time.gmtime()):
                    premium = True
                else:
                    premium = False
                    validuntil = -1

        return {'validuntil': validuntil,
                'trafficleft': trafficleft, 'premium': premium}

    def signin(self, user, password, data):
        html = self.load("http://www.nowvideo.sx/login.php",
                         post={'user': user,
                               'pass': password})

        if re.search(r'>Log In<', html):
            self.fail_login()
