# -*- coding: utf-8 -*-

import re
import time

from module.plugins.Account import Account
from module.utils import parseFileSize


class EgoFilesCom(Account):
    __name__ = "EgoFilesCom"
    __type__ = "account"
    __version__ = "0.2"

    __description__ = """Egofiles.com account plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    PREMIUM_ACCOUNT_PATTERN = '<br/>\s*Premium: (?P<P>[^/]*) / Traffic left: (?P<T>[\d.]*) (?P<U>\w*)\s*\\n\s*<br/>'


    def loadAccountInfo(self, user, req):
        html = req.load("http://egofiles.com")
        if 'You are logged as a Free User' in html:
            return {"premium": False, "validuntil": None, "trafficleft": None}

        m = re.search(self.PREMIUM_ACCOUNT_PATTERN, html)
        if m:
            validuntil = int(time.mktime(time.strptime(m.group('P'), "%Y-%m-%d %H:%M:%S")))
            trafficleft = parseFileSize(m.group('T'), m.group('U')) / 1024
            return {"premium": True, "validuntil": validuntil, "trafficleft": trafficleft}
        else:
            self.logError('Unable to retrieve account information - Plugin may be out of date')

    def login(self, user, data, req):
        # Set English language
        req.load("https://egofiles.com/ajax/lang.php?lang=en", just_header=True)

        html = req.load("http://egofiles.com/ajax/register.php",
                        post={"log": 1,
                              "loginV": user,
                              "passV": data['password']})
        if 'Login successful' not in html:
            self.wrongPassword()
