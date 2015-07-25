# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account


class MegasharesCom(Account):
    __name__    = "MegasharesCom"
    __type__    = "account"
    __version__ = "0.05"
    __status__  = "testing"

    __description__ = """Megashares.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    VALID_UNTIL_PATTERN = r'<p class="premium_info_box">Period Ends: (\w{3} \d{1,2}, \d{4})</p>'


    def parse_info(self, user, password, data, req):
        # self.relogin(user)
        html = self.load("http://d01.megashares.com/myms.php")

        premium = False if '>Premium Upgrade<' in html else True

        validuntil = trafficleft = -1
        try:
            timestr = re.search(self.VALID_UNTIL_PATTERN, html).group(1)
            self.log_debug(timestr)
            validuntil = time.mktime(time.strptime(timestr, "%b %d, %Y"))
        except Exception, e:
            self.log_error(e)

        return {'validuntil': validuntil, 'trafficleft': -1, 'premium': premium}


    def login(self, user, password, data, req):
        html = self.load('http://d01.megashares.com/myms_login.php',
                         post={'httpref'       : "",
                               'myms_login'    : "Login",
                               'mymslogin_name': user,
                               'mymspassword'  : password})

        if not '<span class="b ml">%s</span>' % user in html:
            self.login_fail()
