# -*- coding: utf-8 -*-

import time
import re
import urlparse

from ..internal.misc import json
from ..internal.XFSAccount import XFSAccount


class UptoboxCom(XFSAccount):
    __name__ = "UptoboxCom"
    __type__ = "account"
    __version__ = "0.22"
    __status__ = "testing"

    __description__ = """Uptobox.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("benbox69", "dev@tollet.me"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "uptobox.com"
    PLUGIN_URL = "http://uptobox.com/"
    LOGIN_URL = "https://login.uptobox.com/"

    PREMIUM_PATTERN = r'Premium member'
    VALID_UNTIL_PATTERN = r"class='expiration-date .+?'>(\d{1,2} [\w^_]+ \d{4})"


    def signin(self, user, password, data):
        html = self.load(self.LOGIN_URL, cookies=self.COOKIES)

        if re.search(self.LOGIN_SKIP_PATTERN, html):
            self.skip_login()

        html = self.load(urlparse.urljoin(self.LOGIN_URL, "logarithme"),
                         post={'op': "login",
                               'redirect': self.PLUGIN_URL,
                               'login': user,
                               'password': password},
                         cookies=self.COOKIES)

        if json.loads(html).get('error'):
            self.fail_login()
