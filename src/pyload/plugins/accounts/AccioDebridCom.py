# -*- coding: utf-8 -*-

import json

import pycurl
from pyload.core.network.http.exceptions import BadHeader

from ..base.multi_account import MultiAccount


def args(**kwargs):
    return kwargs


class AccioDebridCom(MultiAccount):
    __name__ = "AccioDebridCom"
    __type__ = "account"
    __version__ = "0.02"
    __status__ = "testing"

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    __description__ = """Accio-debrid.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("PlugPlus", "accio.debrid@gmail.com")]

    LOGIN_TIMEOUT = -1

    API_URL = "https://www.accio-debrid.com/apiv2/"

    def api_response(self, action, get={}, post={}):
        get['action'] = action

        # Better use pyLoad User-Agent so we don't get blocked
        self.req.http.c.setopt(pycurl.USERAGENT, "pyLoad/%s" % self.pyload.version)

        json_data = self.load(self.API_URL, get=get, post=post)

        return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        res = self.api_response("getHostsList")

        if res['success']:
            return res['value']

        else:
            return []

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
            res = self.api_response("login", args(login=user, password=password))

        except BadHeader as exc:
            if exc.code == 401:
                self.fail_login()

            elif exc.code == 405:
                self.fail(self._("Banned IP"))

            else:
                raise

        if res['response_code'] != "ok":
            cache_info.pop(user, None)
            data['cache_info'] = cache_info
            self.db.store("cache_info", cache_info)

            if res['response_code'] == "INCORRECT_PASSWORD":
                self.fail_login()

            elif res['response_code'] == "UNALLOWED_IP":
                self.fail_login(self._("Banned IP"))

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
