# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account
from module.PyFile import PyFile
from module.plugins.captcha.ReCaptcha import ReCaptcha

from module.plugins.internal.misc import parse_size

from datetime import datetime, timedelta
try:
    import simplejson as json
except ImportError:
    import json

class NitroflareCom(Account):
    __name__    = "NitroflareCom"
    __type__    = "account"
    __version__ = "0.16"
    __status__  = "testing"

    __description__ = """Nitroflare.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"         ),
                       ("GammaC0de",      "nitzo2001[AT]yahoo[DOT]com")]


    VALID_UNTIL_PATTERN  = r'>Time Left</label><strong>(.+?)</'
    TRAFFIC_LEFT_PATTERN = r'>Your Daily Limit</label><strong>(?P<S1>[\d.,]+) (?P<U1>[\w^_]+ )?/ (?P<S2>[\d.,]+) (?P<U2>[\w^_]+)'
    LOGIN_FAIL_PATTERN   = r'"type":"error"'

    TOKEN_PATTERN =   r'name="token" value="(.+?)"'


    def grab_info(self, user, password, data):
        validuntil   = -1
        trafficleft  = None
        premium      = False

        data = json.loads(self.load("https://nitroflare.com/api/v2/getKeyInfo",
                         get={'user': user, 'premiumKey': password}))

	if (data['type'] == 'success'):
            self.log_debug('Expires: ' + data['result']['expiryDate'])
            expires = datetime.strptime(data['result']['expiryDate'], '%Y-%m-%d %H:%M:%S')
            expires.replace(tzinfo=None)
            tdelta = expires - datetime.utcnow()
            timeleft = tdelta.total_seconds()

            if timeleft > 0:
                premium = True
                validuntil = timeleft + time.time()

            trafficleft = data['result']['trafficLeft']

        return {'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'premium'    : premium}


    def signin(self, user, password, data):
        login_url = "https://nitroflare.com/api/v2/getKeyInfo"
        params = {'user': user, 'premiumKey': password}
        self.data = self.load(login_url, get=params)

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
