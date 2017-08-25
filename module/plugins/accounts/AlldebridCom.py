# -*- coding: utf-8 -*-

from ..internal.MultiAccount import MultiAccount
from ..internal.misc import json


class AlldebridCom(MultiAccount):
    __name__ = "AlldebridCom"
    __type__ = "account"
    __version__ = "0.37"
    __status__ = "testing"

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    __description__ = """AllDebrid.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Andy Voigt", "spamsales@online.de"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://alldebrid.com/apiv2.php"

    def api_response(self, action, **kwargs):
        kwargs['action'] = action
        html = self.load(self.API_URL, get=kwargs)
        return json.loads(html)

    def grab_hosters(self, user, password, data):
        return [x for x in self.api_response("supportedHost", domainsOnly=1) if x]

    def grab_info(self, user, password, data):
        validuntil = -1
        premium = False

        json_data = self.api_response("login", username=user, password=password)

        if json_data['success'] is True:
            premium = json_data['user']['isPremium']
            validuntil = json_data['user']['premiumUntil'] or -1

        return {'validuntil': validuntil,
                'trafficleft': -1,
                'premium': premium}

    def signin(self, user, password, data):
        json_data = self.api_response("login", username=user, password=password)

        if json_data['success'] is True:
            data['cookie'] = json_data['user']['cookie']

        else:
            self.log_error(json_data['error'])
            self.fail_login()
