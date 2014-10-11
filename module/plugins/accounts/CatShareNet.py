# -*- coding: utf-8 -*-

import re
from time import mktime, strptime
from module.plugins.Account import Account


class CatShareNet(Account):
    __name__ = "CatShareNet"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """CatShareNet account plugin"""
    __author_name__ = "prOq"
    __author_mail__ = None


    ACCOUNT_INFO_PATTERN = r'class="nav-collapse collapse pull-right">[\s\w<>\=\-\."/:]*\sz.</a></li>\s*<li><a href="/premium">.*\s*<span style="color: red">(.*?)</span>[\s\w<>/]*href="/logout"'
    ACCOUNT_LIFE = r'<div class="span6 pull-right">[\s\w<>\=\-":;]*<span style="font-size:13px;">.*?<strong>(.*?)</strong></span>'


    def loadAccountInfo(self, user, req):
	# Premium accounts wasn't tested!
        self.html = req.load("http://catshare.net/", decode=True)
        m = re.search(self.ACCOUNT_INFO_PATTERN, self.html)
        if m:
	    if "Premium" in m.group(1):
		premium = True
	    else:
        	premium = False

	m = re.search(self.ACCOUNT_LIFE, self.html)
	if m:
	    if "-" in m.group(1):
		validuntil = -1
            else:
		validuntil = mktime(strptime(m.group(1), "%d.%m.%Y"))

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}


    def login(self, user, data, req):
        html = req.load("http://catshare.net/login", post={
            "user_email": user,
            "user_password": data['password'],
	    "remindPassword": 0,
            "user[submit]": "Login"})

        if not '<a href="/logout">Wyloguj</a>' in html:
            self.wrongPassword()

