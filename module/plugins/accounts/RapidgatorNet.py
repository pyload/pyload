# -*- coding: utf-8 -*-

import urlparse

from module.plugins.internal.Account import Account
from module.plugins.internal.misc import json


class RapidgatorNet(Account):
    __name__    = "RapidgatorNet"
    __type__    = "account"
    __version__ = "0.18"
    __status__  = "testing"

    __description__ = """Rapidgator.net account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    API_URL = "http://rapidgator.net/api/user/"


    def grab_info(self, user, password, data):
        validuntil  = None
        trafficleft = None
        premium     = False
        sid         = None

        try:
            sid = data.get('sid', None)

            html = self.load(urlparse.urljoin(self.API_URL, "info"),
                             get={'sid': sid})

            self.log_debug("API:USERINFO", html)

            json_data = json.loads(html)

            if json_data['response_status'] == 200:
                if "reset_in" in json_data['response']:
                    self._schedule_refresh(user, json_data['response']['reset_in'])

                validuntil  = json_data['response']['expire_date']
                trafficleft = float(json_data['response']['traffic_left']) / 1024  #@TODO: Remove `/ 1024` in 0.4.10
                premium     = True
            else:
                self.log_error(json_data['response_details'])

        except Exception, e:
            self.log_error(e, trace=True)

        return {'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'premium'    : premium,
                'sid'        : sid}


    def signin(self, user, password, data):
        try:
            html = self.load(urlparse.urljoin(self.API_URL, "login"),
                             post={'username': user,
                                   'password': password})

            self.log_debug("API:LOGIN", html)

            json_data = json.loads(html)

            if json_data['response_status'] == 200:
                data['sid'] = str(json_data['response']['session_id'])
                return
            else:
                self.log_error(json_data['response_details'])

        except Exception, e:
            self.log_error(e, trace=True)

        self.fail_login()
