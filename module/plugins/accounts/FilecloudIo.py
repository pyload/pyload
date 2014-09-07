# -*- coding: utf-8 -*-

from module.plugins.Account import Account
from module.common.json_layer import json_loads


class FilecloudIo(Account):
    __name__ = "FilecloudIo"
    __type__ = "account"
    __version__ = "0.02"

    __description__ = """FilecloudIo account plugin"""
    __author_name__ = ("zoidberg", "stickell")
    __author_mail__ = ("zoidberg@mujmail.cz", "l.stickell@yahoo.it")


    def loadAccountInfo(self, user, req):
        # It looks like the first API request always fails, so we retry 5 times, it should work on the second try
        for _ in xrange(5):
            rep = req.load("https://secure.filecloud.io/api-fetch_apikey.api",
                           post={"username": user, "password": self.accounts[user]['password']})
            rep = json_loads(rep)
            if rep['status'] == 'ok':
                break
            elif rep['status'] == 'error' and rep['message'] == 'no such user or wrong password':
                self.logError("Wrong username or password")
                return {"valid": False, "premium": False}
        else:
            return {"premium": False}

        akey = rep['akey']
        self.accounts[user]['akey'] = akey  # Saved for hoster plugin
        rep = req.load("http://api.filecloud.io/api-fetch_account_details.api",
                       post={"akey": akey})
        rep = json_loads(rep)

        if rep['is_premium'] == 1:
            return {"validuntil": int(rep['premium_until']), "trafficleft": -1}
        else:
            return {"premium": False}

    def login(self, user, data, req):
        req.cj.setCookie("secure.filecloud.io", "lang", "en")
        html = req.load('https://secure.filecloud.io/user-login.html')

        if not hasattr(self, "form_data"):
            self.form_data = {}

        self.form_data['username'] = user
        self.form_data['password'] = data['password']

        html = req.load('https://secure.filecloud.io/user-login_p.html',
                        post=self.form_data,
                        multipart=True)

        self.logged_in = True if "you have successfully logged in - filecloud.io" in html else False
        self.form_data = {}
