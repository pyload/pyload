# -*- coding: utf-8 -*-
from module.plugins.internal.XFSPAccount import XFSPAccount

class RyushareCom(XFSPAccount):
    __name__ = "RyushareCom"
    __version__ = "0.02"
    __type__ = "account"
    __description__ = """ryushare.com account plugin"""
    __author_name__ = ("zoidberg", "trance4us")
    __author_mail__ = ("zoidberg@mujmail.cz", "")
    
    MAIN_PAGE = "http://ryushare.com/"
    
    def login(self, user, data, req):
        html = req.load("http://ryushare.com/login.python", post={"login": user, "password": data["password"], "op": "login"})
        if 'Incorrect Login or Password' in html or '>Error<' in html:          
            self.wrongPassword()