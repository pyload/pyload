# -*- coding: utf-8 -*-
# @author: zoidberg

from __future__ import absolute_import, division, unicode_literals

import re
from time import mktime, strptime

from future import standard_library

from pyload.plugins.downloader.hoster.base.simplehoster import parse_html_form
from pyload.utils import parse

from .. import Account

standard_library.install_aliases()


class XFSPAccount(Account):
    __name__ = "XFSPAccount"
    __version__ = "0.05"
    __type__ = "account"
    __description__ = """XFileSharingPro base account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    MAIN_PAGE = None

    VALID_UNTIL_PATTERN = r'>Premium.[Aa]ccount expire:</TD><TD><b>([^<]+)</b>'
    TRAFFIC_LEFT_PATTERN = r'>Traffic available today:</TD><TD><b>([^<]+)</b>'

    def load_account_info(self, user, req):
        html = req.load(self.MAIN_PAGE + "?op=my_account", decode=True)

        validuntil = trafficleft = None
        premium = True if '>Renew premium<' in html else False

        found = re.search(self.VALID_UNTIL_PATTERN, html)
        if found:
            premium = True
            trafficleft = -1
            try:
                self.log_debug(found.group(1))
                validuntil = mktime(strptime(found.group(1), "%d %B %Y"))
            except Exception as e:
                self.log_error(e.message)
        else:
            found = re.search(self.TRAFFIC_LEFT_PATTERN, html)
            if found:
                trafficleft = found.group(1)
                if "Unlimited" in trafficleft:
                    premium = True
                else:
                    trafficleft = parse.size(trafficleft) >> 10

        return ({'validuntil': validuntil,
                 'trafficleft': trafficleft,
                 'premium': premium})

    def login(self, user, data, req):
        html = req.load('{}login.html'.format(self.MAIN_PAGE), decode=True)

        action, inputs = parse_html_form('name="FL"', html)
        if not inputs:
            inputs = {'op': "login",
                      'redirect': self.MAIN_PAGE}

        inputs.update({'login': user,
                       'password': data['password']})

        html = req.load(self.MAIN_PAGE, post=inputs, decode=True)

        if 'Incorrect Login or Password' in html or '>Error<' in html:
            self.wrong_password()
