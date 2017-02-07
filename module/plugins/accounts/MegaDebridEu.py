# -*- coding: utf-8 -*-

import time
import pycurl

from module.network.HTTPRequest import BadHeader
from module.plugins.internal.MultiAccount import MultiAccount
from module.plugins.internal.misc import json
from module.plugins.internal.misc import encode

def args(**kwargs):
    return kwargs


class MegaDebridEu(MultiAccount):
    __name__    = "MegaDebridEu"
    __type__    = "account"
    __version__ = "0.27"
    __status__  = "testing"

    __config__ = [("mh_mode"    , "all;listed;unlisted", "Filter hosters to use"        , "all"),
                  ("mh_list"    , "str"                , "Hoster list (comma separated)", ""   ),
                  ("mh_interval", "int"                , "Reload interval in minutes"   , 60   )]

    __description__ = """Mega-debrid.eu account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Devirex Hazzard", "naibaf_11@yahoo.de"        ),
                       ("GammaC0de",       "nitzo2001[AT]yahoo[DOT]com"),
                       ("FoxyDarnec",      "goupildavid[AT]gmail[DOT]com")]

    API_URL = "https://www.mega-debrid.eu/api.php"


    def api_response(self, namespace, get={}, post={}):
        self.req.http.c.setopt(pycurl.USERAGENT, encode('Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'))
        json_data = self.load(self.API_URL + namespace, get=get, post=post)

        return json.loads(json_data)


    def grab_hosters(self, user, password, data):
        hosters = self.api_response("", get={'action': "getHosters"})
        if hosters['response_code'] == "ok":
            return [element[0] for element in hosters['hosters']]
        else:
            self.log_error(_("Unable to retrieve hoster list"))
            return []


    def grab_info(self, user, password, data):
        account = self.api_response("", get={'action'  : 'connectUser',
                                      'login'   : user,
                                      'password': password})

        if account['response_code'] == "ok":
            return {'premium': True, 'validuntil': float(account['vip_end']), 'trafficleft': -1}
        else:
            self.log_error(account)
            return {'premium': False}


    def signin(self, user, password, data):
        try:
            account = self.api_response("", get={'action'  : 'connectUser',
                                                 'login'   : user,
                                                 'password': password})

        except BadHeader, e:
            if e.code == 401:
                self.fail_login()

            else:
                raise

        if account['response_code'] != "ok":
            self.fail_login()
