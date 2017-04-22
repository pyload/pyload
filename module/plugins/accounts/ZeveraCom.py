# -*- coding: utf-8 -*-

import time

from ..internal.MultiAccount import MultiAccount


class ZeveraCom(MultiAccount):
    __name__ = "ZeveraCom"
    __type__ = "account"
    __version__ = "0.36"
    __status__ = "testing"

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    __description__ = """Zevera.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "http://api.zevera.com/jDownloader.ashx"

    def api_response(self, method, user, password=None, **kwargs):
        get_data = {'cmd': method,
                    'login': user,
                    'pass': password}

        get_data.update(kwargs)

        res = self.load(self.API_URL,
                        get=get_data)

        self.log_debug(res)

        if ':' in res:
            res = res.replace(',', '\n')
            return dict((y.strip().lower(), z.strip()) for (y, z) in
                        [x.split(':', 1) for x in res.splitlines() if ':' in x])
        else:
            return res

    def grab_hosters(self, user, password, data):
        res = self.api_response("gethosters", user, password)
        return [x.strip() for x in res.split(',')]

    def grab_info(self, user, password, data):
        validuntil = None
        trafficleft = None
        premium = False

        res = self.api_response("accountinfo", user, password)

        if "No trafic" not in res:
            if res['endsubscriptiondate'] == "Expired!":
                validuntil = time.time()

            else:
                validuntil = time.mktime(time.strptime(res['endsubscriptiondate'], "%Y/%m/%d %H:%M:%S"))
                trafficleft = float(res['availabletodaytraffic']) * 1024 if res['orondaytrafficlimit'] != '0' else -1
                premium = True

        return {'validuntil': validuntil,
                'trafficleft': trafficleft,
                'premium': premium}

    def signin(self, user, password, data):
        if self.api_response("accountinfo", user, password) == "No trafic":
            self.fail_login()

