# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.Account import Account
from module.plugins.internal.Plugin import set_cookie


class FilecloudIo(Account):
    __name__    = "FilecloudIo"
    __type__    = "account"
    __version__ = "0.07"
    __status__  = "testing"

    __description__ = """FilecloudIo account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    def parse_info(self, user, password, data, req):
        #: It looks like the first API request always fails, so we retry 5 times, it should work on the second try
        for _i in xrange(5):
            rep = self.load("https://secure.filecloud.io/api-fetch_apikey.api",
                           post={'username': user, 'password': password})
            rep = json_loads(rep)
            if rep['status'] == "ok":
                break
            elif rep['status'] == "error" and rep['message'] == "no such user or wrong password":
                self.log_error(_("Wrong username or password"))
                return {'valid': False, 'premium': False}
        else:
            return {'premium': False}

        akey = rep['akey']
        self.accounts[user]['akey'] = akey  #: Saved for hoster plugin
        rep = self.load("http://api.filecloud.io/api-fetch_account_details.api",
                        post={'akey': akey})
        rep = json_loads(rep)

        if rep['is_premium'] == 1:
            return {'validuntil': float(rep['premium_until']), 'trafficleft': -1}
        else:
            return {'premium': False}


    def login(self, user, password, data, req):
        set_cookie(req.cj, "secure.filecloud.io", "lang", "en")
        html = self.load('https://secure.filecloud.io/user-login.html')

        if not hasattr(self, "form_data"):
            self.form_data = {}

        self.form_data['username'] = user
        self.form_password = password

        html = self.load('https://secure.filecloud.io/user-login_p.html',
                         post=self.form_data)

        if "you have successfully logged in" not in html:
            self.login_fail()
