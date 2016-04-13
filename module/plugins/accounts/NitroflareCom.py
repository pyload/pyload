# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account
from module.PyFile import PyFile
from module.plugins.captcha.ReCaptcha import ReCaptcha


class NitroflareCom(Account):
    __name__    = "NitroflareCom"
    __type__    = "account"
    __version__ = "0.15"
    __status__  = "testing"

    __description__ = """Nitroflare.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"         ),
                       ("GammaC0de",      "nitzo2001[AT]yahoo[DOT]com")]


    VALID_UNTIL_PATTERN  = r'>Time Left</label><strong>(.+?)</'
    TRAFFIC_LEFT_PATTERN = r'>Your Daily Limit</label><strong>(?P<S1>[\d.,]+) (?P<U1>[\w^_]+ )?/ (?P<S2>[\d.,]+) (?P<U2>[\w^_]+)'
    LOGIN_FAIL_PATTERN   = r'<ul class="errors">\s*<li>'

    TOKEN_PATTERN =   r'name="token" value="(.+?)"'


    def grab_info(self, user, password, data):
        validuntil   = -1
        trafficleft  = None
        premium      = False

        html = self.load("https://nitroflare.com/member",
                         get={'s': "premium"})

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            expiredate = m.group(1).strip()
            self.log_debug("Time Left: " + expiredate)

            try:
                validuntil = sum(int(v) * {'day': 24 * 3600, 'hour': 3600, 'minute': 60}[u.lower()] for v, u in
                                 re.findall(r'(\d+)\s*(day|hour|minute)', expiredate, re.I))

            except Exception, e:
                self.log_error(e, trace=True)

            else:
                self.log_debug("Valid until: %s" % validuntil)

                if validuntil:
                    validuntil += time.time()
                    premium = True
                else:
                    validuntil = -1

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m is not None:
            try:
                trafficleft = self.parse_traffic(m.group('S2'), m.group('U2')) - self.parse_traffic(m.group('S1'), m.group('U1') or "B")

            except Exception, e:
                self.log_error(e, trace=True)
        else:
            self.log_debug("TRAFFIC_LEFT_PATTERN not found")

        return {'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'premium'    : premium}


    def signin(self, user, password, data):
        login_url = "https://nitroflare.com/login"
        post_data = {'login'   : "",
                     'email'   : user,
                     'password': password}

        self.data = self.load(login_url)

        # dummy pyfile
        pyfile = PyFile(self.pyload.files, -1, login_url, login_url, 0, 0, "", self.classname, -1, -1)
        pyfile.plugin = self

        self.captcha = ReCaptcha(pyfile)

        captcha_key = self.captcha.detect_key()
        if captcha_key:
            response, challenge = self.captcha.challenge()
            post_data['g-recaptcha-response'] = response

        token = re.search(self.TOKEN_PATTERN, self.data).group(1)
        post_data['token'] = token

        self.data = self.load("https://nitroflare.com/login", post=post_data)

        if re.search(self.LOGIN_FAIL_PATTERN, self.data):
            self.fail_login()

    """
     @NOTE: below are methods
      necessary for captcha to work with account plugins
    """
    def check_status(self):
        pass

    def retry_captcha(self, attemps=10, wait=1, msg=_("Max captcha retries reached")):
        self.captcha.invalid()
        self.fail_login(msg="Invalid captcha")


