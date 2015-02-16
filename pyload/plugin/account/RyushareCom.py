# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSAccount import XFSAccount


class RyushareCom(XFSAccount):
    __name__    = "RyushareCom"
    __type__    = "account"
    __version__ = "0.05"

    __description__ = """Ryushare.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("trance4us", "")]


    HOSTER_DOMAIN = "ryushare.com"


    def login(self, user, data, req):
        req.lastURL = "http://ryushare.com/login.python"
        html = req.load("http://ryushare.com/login.python",
                        post={"login": user, "password": data['password'], "op": "login"})
        if 'Incorrect Login or Password' in html or '>Error<' in html:
            self.wrongPassword()
