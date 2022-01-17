# -*- coding: utf-8 -*-

import json

from ..base.multi_account import MultiAccount


class PremiumizeMe(MultiAccount):
    __name__ = "PremiumizeMe"
    __type__ = "account"
    __version__ = "0.32"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter downloaders to use", "all"),
        ("mh_list", "str", "Downloader list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Premiumize.me account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Florian Franzen", "FlorianFranzen@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://www.premiumize.me/api
    API_URL = "https://www.premiumize.me/api/"

    def api_respond(self, method, **kwargs):
        json_data = self.load(self.API_URL + method, get=kwargs)

        return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        res = self.api_respond("services/list", apikey=password)

        hosters = []
        for _h in res['directdl']:
            hosters += res['aliases'][_h]

        return hosters

    def grab_info(self, user, password, data):
        validuntil = None
        trafficleft = None
        premium = False

        res = self.api_respond("account/info", apikey=password)

        if res['status'] == "success":
            premium = res['premium_until'] is not False

            if premium:
                validuntil = res['premium_until']
                trafficleft = -1

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        res = self.api_respond("account/info", apikey=password)

        if res['status'] != "success":
            self.log_error(
                self._("Password for premiumize.me should be the API token - get it from: https://www.premiumize.me/account")
            )

            self.fail_login(res['message'])

        elif res['customer_id'] != user:
            self.log_error(
                self._("username for premiumize.me should be the Customer ID - get it from: https://www.premiumize.me/account")
            )

            self.fail_login()
