# -*- coding: utf-8 -*-

import re
import time
import urlparse

from module.plugins.internal.Account import Account
from module.plugins.internal.misc import parse_html_form


class EuroshareEu(Account):
    __name__    = "EuroshareEu"
    __type__    = "account"
    __version__ = "0.10"
    __status__  = "testing"

    __description__ = """Euroshare.eu account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"        ),
                       ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]


    def grab_info(self, user, password, data):
        html = self.load("http://euroshare.eu/",
                         get={'lang': "en"})

        m = re.search(r'<span title="Premium do: (\d+\.\d+\.\d+ \d+:\d+:\d+)"', html)
        if m is None:
            premium    = False
            validuntil = -1
        else:
            premium = True
            validuntil = time.mktime(time.strptime(m.group(1), "%d.%m.%Y %H:%M:%S"))

        return {'validuntil': validuntil, 'trafficleft': -1, 'premium': premium}


    def signin(self, user, password, data):
        login_url = "http://euroshare.eu/user/login/"
        html = self.load(login_url,
                         get={'lang' : "en"})

        if r'<li class="logout">' in html:
            self.skip_login()

        action, inputs = parse_html_form('id="frm-prihlaseni"', html)
        if not inputs:
            self.fail_login(_("Login form not found"))

        inputs['username'] = user
        inputs['password'] = password

        html = self.load(urlparse.urljoin(login_url, action),
                         post=inputs)

        if r'<li class="logout">' not in html:
            self.fail_login()
