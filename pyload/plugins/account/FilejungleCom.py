# -*- coding: utf-8 -*-

import re
from time import mktime, strptime

from pyload.plugins.Account import Account


class FilejungleCom(Account):
    __name    = "FilejungleCom"
    __type    = "account"
    __version = "0.11"

    __description = """Filejungle.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    login_timeout = 60

    URL = "http://filejungle.com/"
    TRAFFIC_LEFT_PATTERN = r'"/extend_premium\.php">Until (\d+ \w+ \d+)<br'
    LOGIN_FAILED_PATTERN = r'<span htmlfor="loginUser(Name|Password)" generated="true" class="fail_info">'


    def loadAccountInfo(self, user, req):
        html = req.load(self.URL + "dashboard.php")
        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            premium = True
            validuntil = mktime(strptime(m.group(1), "%d %b %Y"))
        else:
            premium = False
            validuntil = -1

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}


    def login(self, user, data, req):
        html = req.load(self.URL + "login.php", post={
            "loginUserName": user,
            "loginUserPassword": data['password'],
            "loginFormSubmit": "Login",
            "recaptcha_challenge_field": "",
            "recaptcha_response_field": "",
            "recaptcha_shortencode_field": ""})

        if re.search(self.LOGIN_FAILED_PATTERN, html):
            self.wrongPassword()
