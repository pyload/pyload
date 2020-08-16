# -*- coding: utf-8 -*-

import re
import time

from ..base.account import BaseAccount


class MegasharesCom(BaseAccount):
    __name__ = "MegasharesCom"
    __type__ = "account"
    __version__ = "0.11"
    __status__ = "testing"

    __description__ = """Megashares.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    VALID_UNTIL_PATTERN = (
        r'<p class="premium_info_box">Period Ends: (\w{3} \d{1,2}, \d{4})</p>'
    )

    def grab_info(self, user, password, data):
        html = self.load("http://d01.megashares.com/myms.php")

        premium = ">Premium Upgrade<" not in html

        validuntil = trafficleft = -1
        try:
            timestr = re.search(self.VALID_UNTIL_PATTERN, html).group(1)
            self.log_debug(timestr)
            validuntil = time.mktime(time.strptime(timestr, "%b %d, %Y"))

        except Exception as exc:
            self.log_error(
                exc, exc_info=self.pyload.debug > 1, stack_info=self.pyload.debug > 2
            )

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def signin(self, user, password, data):
        html = self.load(
            "http://d01.megashares.com/myms_login.php",
            post={
                "httpref": "",
                "myms_login": "Login",
                "mymslogin_name": user,
                "mymspassword": password,
            },
        )

        if '<span class="b ml">{}</span>'.format(user) not in html:
            self.fail_login()
