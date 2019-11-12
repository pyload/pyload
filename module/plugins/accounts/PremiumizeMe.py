# -*- coding: utf-8 -*-

from ..internal.misc import json
from ..internal.MultiAccount import MultiAccount


class PremiumizeMe(MultiAccount):
    __name__ = "PremiumizeMe"
    __type__ = "account"
    __version__ = "0.32"
    __status__ = "testing"

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    __description__ = """Premiumize.me account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Florian Franzen", "FlorianFranzen@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    # See https://www.premiumize.me/api
    API_URL = "https://www.premiumize.me/api/"

    def api_respond(self, method, **kwargs):
        json_data = self.load(self.API_URL + method, get=kwargs)

        return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        res = self.api_respond("services/list", apikey=password)
        return res['directdl'] + reduce(lambda x, y: x + y, [res['aliases'][_h] if _h in res['aliases'] else []
                                                             for _h in res['directdl']])

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

        return {'validuntil': validuntil,
                'trafficleft': trafficleft,
                'premium': premium}

    def signin(self, user, password, data):
        res = self.api_respond("account/info", apikey=password)

        if res['status'] != "success":
            self.log_error(_("Password for premiumize.me should be the API token - get it from: https://www.premiumize.me/account"))
            self.fail_login(res['message'])

        elif res['customer_id'] != user:
            self.log_error(_("username for premiumize.me should be the Customer ID - get it from: https://www.premiumize.me/account"))
            self.fail_login()
