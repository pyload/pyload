# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account
from module.common.json_layer import json_loads


class RapiduNet(Account):
    __name__    = "RapiduNet"
    __type__    = "account"
    __version__ = "0.07"
    __status__  = "testing"

    __description__ = """Rapidu.net account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("prOq", None),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    PREMIUM_PATTERN = r'>Account: <b>Premium'

    VALID_UNTIL_PATTERN = r'>Account: <b>\w+ \((\d+)'

    TRAFFIC_LEFT_PATTERN = r'class="tipsyS"><b>(.+?)<'


    def parse_info(self, user, password, data, req):
        validuntil  = None
        trafficleft = -1
        premium     = False

        html = self.load("https://rapidu.net/")

        if re.search(self.PREMIUM_PATTERN, html):
            premium = True

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            validuntil = time.time() + (86400 * int(m.group(1)))

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            trafficleft = self.parse_traffic(m.group(1))

        return {'validuntil': validuntil, 'trafficleft': trafficleft, 'premium': premium}


    def login(self, user, password, data, req):
        self.load("https://rapidu.net/ajax.php",
                  get={'a': "getChangeLang"},
                  post={'_go' : "",
                        'lang': "en"})

        json = json_loads(self.load("https://rapidu.net/ajax.php",
                                    get={'a': "getUserLogin"},
                                    post={'_go'     : "",
                                          'login'   : user,
                                          'pass'    : password,
                                          'remember': "1"}))

        self.log_debug(json)

        if not json['message'] == "success":
            self.login_fail()
