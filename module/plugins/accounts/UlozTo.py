# -*- coding: utf-8 -*-

import pycurl
import re
import time
import urlparse

from ..internal.Account import Account
from ..internal.misc import json


class UlozTo(Account):
    __name__ = "UlozTo"
    __type__ = "account"
    __version__ = "0.28"
    __status__ = "testing"

    __description__ = """Uloz.to account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("pulpe", None),
                   ("ondrej", "git@ondrej.it"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    INFO_PATTERN = r'title="credit in use"><\/span>\s*([\d.,]+) ([\w^_]+)\s*<\/td>\s*<td class="right">([\d.]+)<\/td>'

    def grab_info(self, user, password, data):
        current_millis = int(time.time() * 1000)
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        try:
            html = json.loads(self.load("https://ulozto.net/statistiky",
                                        get={'do': "overviewPaymentsView-ajaxLoad",
                                             '_': current_millis}
                              ))['snippets']['snippet-overviewPaymentsView-']

        except (ValueError, KeyError):
            self.log_error(_("Unable to retrieve account information, unexpected response"))
            return {'validuntil': None,
                    'trafficleft': None,
                    'premium': False}

        if ">You don't have any credit at the moment.<" in html:  #: Free account
            validuntil = -1
            trafficleft = -1
            premium = False

        else:
            m = re.search(self.INFO_PATTERN, html)
            if m is not None:
                validuntil = time.mktime(time.strptime(m.group(3) + " 23:59:59", '%d.%m.%Y %H:%M:%S'))
                trafficleft = self.parse_traffic(m.group(1), m.group(2))
                premium = True if trafficleft else False

            else:
                self.log_error(_("Unable to retrieve account information, pattern not found"))
                validuntil = None
                trafficleft = None
                premium = False

        return {'validuntil': validuntil,
                'trafficleft': trafficleft,
                'premium': premium}

    def signin(self, user, password, data):
        login_page = self.load('https://www.ulozto.net/?do=web-login')
        if ">Log out<" in login_page:
            self.skip_login()

        action = re.findall('<form action="(.+?)"', login_page)[1].replace('&amp;', '&')
        token = re.search('_token_" value="(.+?)"', login_page).group(1)

        html = self.load(urlparse.urljoin("https://www.ulozto.net/", action),
                         post={'_token_': token,
                               '_do': "loginForm-submit",
                               'login': u"Submit",
                               'password': password,
                               'username': user})

        if '<div class="flash error">' in html:
            self.fail_login()
