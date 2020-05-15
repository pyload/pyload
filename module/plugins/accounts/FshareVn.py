# -*- coding: utf-8 -*-

import pycurl
from module.network.HTTPRequest import BadHeader

from ..internal.Account import Account
from ..internal.misc import json


class FshareVn(Account):
    __name__ = "FshareVn"
    __type__ = "account"
    __version__ = "0.25"
    __status__ = "testing"

    __description__ = """Fshare.vn account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"),
                   ("stickell", "l.stickell@yahoo.it"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_KEY = "L2S7R6ZMagggC5wWkQhX2+aDi467PPuftWUMRFSn"
    API_URL = "https://api.fshare.vn/api/"

    def api_response(self, method, session_id=None, **kwargs):
        self.req.http.c.setopt(pycurl.USERAGENT, "okhttp/3.6.0")

        if len(kwargs) == 0:
            json_data = self.load(self.API_URL + method,
                                  cookies=[("fshare.vn", 'session_id', session_id)] if session_id else True)

        else:
            json_data = self.load(self.API_URL + method,
                                  post=json.dumps(kwargs),
                                  cookies=[("fshare.vn", 'session_id', session_id)] if session_id else True)

        return json.loads(json_data)

    def grab_info(self, user, password, data):
        trafficleft = None
        premium = False

        api_data = self.api_response("user/get", session_id=data['session_id'])

        expire_vip = unicode(api_data.get("expire_vip", ""))  #: isnumeric() is only available for unicode strings
        validuntil = float(expire_vip) if expire_vip.isnumeric() else None

        if validuntil:
            premium = True

        return {'validuntil': validuntil,
                'trafficleft': trafficleft,
                'premium': premium}

    def signin(self, user, password, data):
        user = user.lower()

        fshare_session_cache = self.db.retrieve("fshare_session_cache") or {}
        if user in fshare_session_cache:
            data['token'] = fshare_session_cache[user]['token']
            data['session_id'] = fshare_session_cache[user]['session_id']

            try:
                api_data = self.api_response("user/get", session_id=data['session_id'])

            except BadHeader, e:
                if e.code == 401:
                    del fshare_session_cache[user]
                    self.db.store("fshare_session_cache", fshare_session_cache)

            if api_data.get('email', "").lower() == user:
                self.skip_login()

            else:
                del fshare_session_cache[user]
                self.db.store("fshare_session_cache", fshare_session_cache)

        data['token'] = None
        data['session_id'] = None

        try:
            api_data = self.api_response("user/login",
                                         app_key=self.API_KEY,
                                         user_email=user,
                                         password=password)
        except BadHeader, e:
            self.fail_login()

        if api_data['code'] != 200:
            self.log_error(api_data['msg'])
            self.fail_login()

        fshare_session_cache[user] = {'token': api_data['token'],
                                    'session_id': api_data['session_id']}
        self.db.store("fshare_session_cache", fshare_session_cache)

        data['token'] = fshare_session_cache[user]['token']
        data['session_id'] = fshare_session_cache[user]['session_id']
