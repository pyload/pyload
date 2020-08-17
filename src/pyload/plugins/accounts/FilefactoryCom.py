# -*- coding: utf-8 -*-

import re
import time

from ..base.account import BaseAccount


class FilefactoryCom(BaseAccount):
    __name__ = "FilefactoryCom"
    __type__ = "account"
    __version__ = "0.23"
    __status__ = "testing"

    __description__ = """Filefactory.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    VALID_UNTIL_PATTERN = r"Premium valid until: <strong>(?P<D>\d{1,2})\w{1,2} (?P<M>\w{3}), (?P<Y>\d{4})</strong>"

    def grab_info(self, user, password, data):
        html = self.load("http://www.filefactory.com/account/")

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            premium = True
            validuntil = re.sub(
                self.VALID_UNTIL_PATTERN, r"\g<D> \g<M> \g<Y>", m.group(0)
            )
            validuntil = time.mktime(time.strptime(validuntil, "%d %b %Y"))

        else:
            premium = False
            validuntil = -1

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}

    def signin(self, user, password, data):
        html = self.load("https://www.filefactory.com/member/signin.php")
        if "/member/signout.php" in html:
            self.skip_login()

        html = self.load(
            "https://www.filefactory.com/member/signin.php",
            post={"loginEmail": user, "loginPassword": password, "Submit": "Sign In"},
        )

        if "/member/signout.php" not in html:
            self.fail_login()
