# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount


class RyushareCom(XFSPAccount):
    __name__ = "RyushareCom"
    __type__ = "account"
    __version__ = "0.04"

    __description__ = """Ryushare.com account plugin"""
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("trance4us", None)]


    HOSTER_URL = "http://www.ryushare.com/"


    def login(self, user, data, req):
        req.lastURL = "http://ryushare.com/login.python"
        html = req.load("http://ryushare.com/login.python",
                        post={"login": user, "password": data['password'], "op": "login"})
        if 'Incorrect Login or Password' in html or '>Error<' in html:
            self.wrongPassword()
