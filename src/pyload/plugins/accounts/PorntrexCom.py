# -*- coding: utf-8 -*-

from ..base.account import BaseAccount
from ..helpers import parse_html_form


class PorntrexCom(BaseAccount):
    # Actually not needed
    __name__ = "PorntrexCom"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __description__ = """Porntrex.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("ondrej", "git@ondrej.it")]

    def grab_info(self, user, password, data):
        return {
            "validuntil": -1,
            "trafficleft": -1,
        }

    def signin(self, user, password, data):
        html = self.load("https://www.porntrex.com")
        if ">Log out<" in html:
            self.skip_login()

        url, inputs = parse_html_form(
            'action="https://www.porntrex.com/ajax-login/"', html
        )
        if inputs is None:
            self.fail_login("Login form not found")

        inputs["username"] = user
        inputs["pass"] = password

        html = self.load(url, post=inputs)
        if ">Log out<" not in html:
            self.fail_login()
