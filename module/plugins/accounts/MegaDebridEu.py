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
    __version__ = "0.37"
    __status__ = "testing"

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    __description__ = """Mega-debrid.eu account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Devirex Hazzard", "naibaf_11@yahoo.de"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
                   ("FoxyDarnec", "goupildavid[AT]gmail[DOT]com")]

    LOGIN_TIMEOUT = -1

    API_URL = "https://www.mega-debrid.eu/api.php"

    def api_response(self, action, get={}, post={}):
        get['action'] = action

        # Better use pyLoad User-Agent so we don't get blocked
        self.req.http.c.setopt(pycurl.USERAGENT, encode("pyLoad/%s" % self.pyload.version))

        json_data = self.load(self.API_URL, get=get, post=post)

        return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        hosters = []
        try:
            res = self.api_response("getHostersList")

        except BadHeader, e:
            if e.code == 405:
                self.log_error(_("Unable to retrieve hosters list: Banned IP"))

            else:
                self.log_error(_("Unable to retrieve hosters list: error %s"), e.code)

        else:
            if res['response_code'] == "ok":
                hosters = reduce((lambda x, y: x + y), [_h['domains'] for _h in res['hosters']
                                                        if 'domains' in _h and isinstance(_h['domains'], list)])

            else:
                self.log_error(_("Unable to retrieve hoster list: %s") % res['response_text'])

        return hosters

    def grab_info(self, user, password, data):
        validuntil = None
        trafficleft = None
        premium = False

        cache_info = data.get('cache_info', {})
        if user in cache_info:
            validuntil = float(cache_info[user]['vip_end'])
            premium = validuntil > 0
            trafficleft = -1

        return {'validuntil': validuntil,
                'trafficleft': trafficleft,
                'premium': premium}

    def signin(self, user, password, data):
        cache_info = self.db.retrieve("cache_info", {})
        if user in cache_info:
            data['cache_info'] = cache_info
            self.skip_login()

        try:
            res = self.api_response("connectUser", args(login=user, password=password))

        except BadHeader, e:
            if e.code == 401:
                self.fail_login()

            elif e.code == 405:
                self.fail(_("Banned IP"))

            else:
                raise

        if res['response_code'] != "ok":
            cache_info.pop(user, None)
            data['cache_info'] = cache_info
            self.db.store("cache_info", cache_info)

            if res['response_code'] == "UNKNOWN_USER":
                self.fail_login()

            elif res['response_code'] == "UNALLOWED_IP":
                self.fail_login(_("Banned IP"))

            else:
                self.log_error(res['response_text'])
                self.fail_login(res['response_text'])

        else:
            cache_info[user] = {'vip_end': res['vip_end'],
                                'token': res['token']}
            data['cache_info'] = cache_info

            self.db.store("cache_info", cache_info)

    def relogin(self):
        if self.req:
            cache_info = self.info['data'].get('cache_info', {})

            cache_info.pop(self.user, None)
            self.info['data']['cache_info'] = cache_info
            self.db.store("cache_info", cache_info)

        return MultiAccount.relogin(self)