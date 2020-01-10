# -*- coding: utf-8 -*-

from module.network.HTTPRequest import BadHeader

from ..internal.misc import json
from ..internal.MultiAccount import MultiAccount


class AlldebridCom(MultiAccount):
    __name__ = "AlldebridCom"
    __type__ = "account"
    __version__ = "0.43"
    __status__ = "testing"

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12),
                  ("ignore_status", "bool", "Treat all hosters as available (ignore status field)", False)]

    __description__ = """AllDebrid.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Andy Voigt", "spamsales@online.de"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    # See https://docs.alldebrid.com/
    API_URL = "https://api.alldebrid.com/"

    def api_response(self, method, **kwargs):
        kwargs.update({'agent': "pyLoad",
                       'version': self.pyload.version})
        json_data = self.load(self.API_URL + method, get=kwargs)
        return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        json_data = self.api_response("user/hosts", token=password)
        if json_data.get("error", False):
            return []

        else:
            valid_statuses = (True, False) if self.config.get("ignore_status") is True else (True,)
            return reduce(lambda x, y: x + y,
                          [[_h['domain']] + _h.get('altDomains', [])
                           for _h in json_data['hosts'].values()
                           if _h['status'] in valid_statuses])

    def grab_info(self, user, password, data):
        json_data = self.api_response("user/login", token=password)

        if json_data.get("error", False):
            premium = False
            validuntil = -1

        else:
            premium = json_data['user']['isPremium']
            validuntil = json_data['user']['premiumUntil'] or -1

        return {'validuntil': validuntil,
                'trafficleft': -1,
                'premium': premium}

    def signin(self, user, password, data):
        try:
            json_data = self.api_response("user/login",token=password)

        except BadHeader, e:
            if e.code == 401:
                self.log_error(_("Password for alldebrid.com should be the API token - use GetAlldebridToken.py to get it: https://github.com/pyload/pyload/files/3100409/GetAlldebridToken.zip"))
                self.fail_login()

            else:
                raise


        if json_data.get("error", False):
            self.log_error(_("Password for alldebrid.com should be the API token - use GetAlldebridToken.py to get it: https://github.com/pyload/pyload/files/3100409/GetAlldebridToken.zip"))
            self.fail_login(json_data['error'])

        elif json_data['user']['username'] != user:
            self.fail_login(_("username for alldebrid.com should be your alldebrid.com username"))
            self.fail_login()
