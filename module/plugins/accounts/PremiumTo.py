# -*- coding: utf-8 -*-

from ..internal.MultiAccount import MultiAccount
from ..internal.misc import json


class PremiumTo(MultiAccount):
    __name__ = "PremiumTo"
    __type__ = "account"
    __version__ = "0.21"
    __status__ = "testing"

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    __description__ = """Premium.to account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.net"),
                   ("zoidberg", "zoidberg@mujmail.cz"),
                   ("stickell", "l.stickell@yahoo.it"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]


    # See https://premium.to/API.html
    API_URL = "http://api.premium.to/api/2/"

    def api_response(self, method, **kwargs):
        return json.loads(self.load(self.API_URL + method + ".php",
                                    get=kwargs))

    def grab_hosters(self, user, password, data):
        json_data = self.api_response("hosts", userid=user, apikey=password)
        return json_data['hosts'] if json_data.get('code') == 200 else []

    def grab_info(self, user, password, data):
        json_data = self.api_response("traffic", userid=user, apikey=password)

        if json_data.get('code') == 200:
            trafficleft = float(json_data['traffic'] + json_data['specialtraffic'])
            return {'premium': True,
                    'trafficleft': trafficleft,
                    'validuntil': -1}

        else:
            return {'premium': False,
                    'trafficleft': None,
                    'validuntil': None}

    def signin(self, user, password, data):
        json_data = self.api_response("traffic", userid=user, apikey=password)

        if json_data['code'] != 200:
            self.log_warning(_("Username and password for PremiumTo should be the API userid & apikey"),
                             _("Trying via username and password"))

            json_data = self.api_response("getapicredentials", username=user, password=password)
            if not json_data.get('userid') or not json_data.get('userid'):
                self.log_warning(json_data['message'])
                self.fail_login()

            else:
                # Replace current user & password with the generated userid & apikey
                # Hacky hack, but what can we do?!
                userid = json_data['userid']
                apikey = json_data['apikey']
                plugin = self.classname
                self.pyload.accountManager.accounts[plugin][userid] = self.pyload.accountManager.accounts[plugin].pop(user)
                self.pyload.accountManager.accounts[plugin][userid]['password'] = apikey
                self.user = userid
                self.info['data']['login'] = userid
                self.info['login']['password'] = apikey

