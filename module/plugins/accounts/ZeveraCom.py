# -*- coding: utf-8 -*-

import datetime
import time

from ..internal.misc import json
from ..internal.MultiAccount import MultiAccount


class ZeveraCom(MultiAccount):
    __name__ = "ZeveraCom"
    __type__ = "account"
    __version__ = "0.38"
    __status__ = "testing"

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    __description__ = """Zevera.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://www.zevera.com/api/"

    def api_response(self, method, api_key, **kwargs):
        get_data = {'client_id': "452508742",
                    'apikey': api_key}

        get_data.update(kwargs)

        res = self.load(self.API_URL + method,
                        get=get_data)

        return json.loads(res)

    def grab_hosters(self, user, password, data):
        res = self.api_response("services/list", password)
        return res['directdl']

    def grab_info(self, user, password, data):
        trafficleft = None

        res = self.api_response("account/info", password)

        premium = res['premium_until'] is not False
        validuntil = time.mktime(datetime.datetime.fromtimestamp(res['premium_until']).timetuple()) if premium else -1

        return {'validuntil': validuntil,
                'trafficleft': trafficleft,
                'premium': premium}

    def signin(self, user, password, data):
        res = self.api_response("account/info", password)
        if res['status'] != "success":
            self.log_error( _("Password for Zevera should be the API token - get it from: https://www.zevera.com/account"))
            self.fail_login()
