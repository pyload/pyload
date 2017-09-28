# -*- coding: utf-8 -*-

import urlparse

from ..internal.Account import Account
from ..internal.misc import json


class RapidgatorNet(Account):
    __name__ = "RapidgatorNet"
    __type__ = "account"
    __version__ = "0.24"
    __status__ = "testing"

    __description__ = """Rapidgator.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    TUNE_TIMEOUT = False

    API_URL = "https://rapidgator.net/api/user/"

    def api_response(self, method, **kwargs):
        json_data = self.load(self.API_URL + method,
                              get=kwargs)
        return json.loads(json_data)

    def grab_info(self, user, password, data):
        validuntil = None
        trafficleft = None
        premium = False

        try:
            json_data = self.api_response("info", sid=data['sid'])

            if json_data['response_status'] == 200:
                validuntil = json_data['response']['expire_date']
                # @TODO: Remove `/ 1024` in 0.4.10
                trafficleft = float(json_data['response']['traffic_left']) / 1024
                premium = True

            else:
                self.log_error(json_data['response_details'])

        except Exception, e:
            self.log_error(e, trace=True)

        return {'validuntil': validuntil,
                'trafficleft': trafficleft,
                'premium': premium}

    def signin(self, user, password, data):
        try:
            json_data = self.api_response("login", username=user, password=password)

            if json_data['response_status'] == 200:
                data['sid'] = str(json_data['response']['session_id'])

                if 'reset_in' in json_data['response']:
                    self.timeout = float(json_data['response']['reset_in'])
                    self.TUNE_TIMEOUT = False

                else:
                    self.TUNE_TIMEOUT = True

                return

            else:
                self.log_error(json_data['response_details'])

        except Exception, e:
            self.log_error(e, trace=True)

        self.fail_login()
