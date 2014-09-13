# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPAccount import XFSPAccount
from module.plugins.internal.SimpleHoster import parseHtmlForm


class CyberlockerCh(XFSPAccount):
    __name__ = "CyberlockerCh"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Cyberlocker.ch account plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    MAIN_PAGE = "http://cyberlocker.ch/"


    def login(self, user, data, req):
        html = req.load(self.MAIN_PAGE + 'login.html', decode=True)

        action, inputs = parseHtmlForm('name="FL"', html)
        if not inputs:
            inputs = {"op": "login",
                      "redirect": self.MAIN_PAGE}

        inputs.update({"login": user,
                       "password": data['password']})

        # Without this a 403 Forbidden is returned
        req.http.lastURL = self.MAIN_PAGE + 'login.html'
        html = req.load(self.MAIN_PAGE, post=inputs, decode=True)

        if 'Incorrect Login or Password' in html or '>Error<' in html:
            self.wrongPassword()
