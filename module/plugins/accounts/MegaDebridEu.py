# -*- coding: utf-8 -*-

import pycurl
from module.network.HTTPRequest import BadHeader

from ..internal.misc import encode, json, reduce
from ..internal.MultiAccount import MultiAccount


def args(**kwargs):
    return kwargs


class MegaDebridEu(MultiAccount):
    __name__ = "MegaDebridEu"
    __type__ = "account"
    __version__ = "0.30"
    __status__ = "testing"

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in minutes", 60)]

    __description__ = """Mega-debrid.eu account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Devirex Hazzard", "naibaf_11@yahoo.de"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
                   ("FoxyDarnec", "goupildavid[AT]gmail[DOT]com")]

    API_URL = "https://www.mega-debrid.eu/api.php"

    def api_response(self, action, get={}, post={}):
        get['action'] = action
        self.req.http.c.setopt(pycurl.USERAGENT, encode(self.config.get("useragent",
                                                                        default="Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:51.0) Gecko/20100101 Firefox/51.0",
                                                                        plugin="UserAgentSwitcher")))
        json_data = self.load(self.API_URL, get=get, post=post)

        return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        hosters = self.api_response("getHosters")

        if hosters['response_code'] == "ok":
            return reduce((lambda x, y: x + y), hosters['hosters'])

        else:
            self.log_error(_("Unable to retrieve hoster list"))
            return []

    def grab_info(self, user, password, data):
        validuntil = None
        trafficleft = None
        premium = False

        res = self.api_response(
            "connectUser", args(
                login=user, password=password))

        if res['response_code'] == "ok":
            validuntil = float(res['vip_end'])
            premium = validuntil > 0
            trafficleft = -1

        else:
            self.log_error(res['response_text'])

        data['token'] = res['token']

        return {'validuntil': validuntil,
                'trafficleft': trafficleft, 'premium': premium}

    def signin(self, user, password, data):
        try:
            res = self.api_response(
                "connectUser", args(
                    login=user, password=password))

        except BadHeader, e:
            if e.code == 401:
                self.fail_login()

            else:
                raise

        if res['response_code'] != "ok":
            self.fail_login()

        data['token'] = res['token']
