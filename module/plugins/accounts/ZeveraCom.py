# -*- coding: utf-8 -*-

import time

from module.plugins.internal.MultiAccount import MultiAccount


class ZeveraCom(MultiAccount):
    __name__    = "ZeveraCom"
    __type__    = "account"
    __version__ = "0.32"
    __status__  = "testing"

    __config__ = [("mh_mode"    , "all;listed;unlisted", "Filter hosters to use"        , "all"),
                  ("mh_list"    , "str"                , "Hoster list (comma separated)", ""   ),
                  ("mh_interval", "int"                , "Reload interval in minutes"   , 60   )]

    __description__ = """Zevera.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    PLUGIN_DOMAIN = "zevera.com"


    def grab_hosters(self, user, password, data):
        html = self.api_response(user, password, cmd="gethosters")
        return [x.strip() for x in html.split(",")]


    def __init__(self, manager, accounts):  #@TODO: remove in 0.4.10
        self.init()
        return super(ZeveraCom, self).__init__(manager, accounts)


    def init(self):
        if not self.PLUGIN_DOMAIN:
            self.log_error(_("Missing PLUGIN_DOMAIN"))

        if not hasattr(self, "API_URL"):
            self.API_URL = "http://api.%s/jDownloader.ashx" % (self.PLUGIN_DOMAIN or "")


    def grab_info(self, user, password, data):
        validuntil  = None
        trafficleft = None
        premium     = False

        api = self.api_response(user, password)

        if "No trafic" not in api and api['endsubscriptiondate'] != "Expired!":
            validuntil  = time.mktime(time.strptime(api['endsubscriptiondate'], "%Y/%m/%d %H:%M:%S"))
            trafficleft = float(api['availabletodaytraffic']) * 1024 if api['orondaytrafficlimit'] != '0' else -1
            premium     = True

        return {'validuntil': validuntil, 'trafficleft': trafficleft, 'premium': premium}


    def signin(self, user, password, data):
        if self.api_response(user, password) == "No trafic":
            self.fail_login()


    def api_response(self, user, password=None, just_header=False, **kwargs):
        get_data = {'cmd'  : "accountinfo",
                    'login': user,
                    'pass' : password}

        get_data.update(kwargs)

        res = self.load(self.API_URL,
                        get=get_data,
                        just_header=just_header)

        self.log_debug(res)

        if ':' in res:
            if not just_header:
                res = res.replace(',', '\n')
            return dict((y.strip().lower(), z.strip()) for (y, z) in
                        [x.split(':', 1) for x in res.splitlines() if ':' in x])
        else:
            return res
