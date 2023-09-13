# -*- coding: utf-8 -*-
import json

import pycurl
from pyload.core.network.http.exceptions import BadHeader

from ..base.account import BaseAccount


class FshareVn(BaseAccount):
    __name__ = "FshareVn"
    __type__ = "account"
    __version__ = "0.28"
    __status__ = "testing"

    __description__ = """Fshare.vn account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    API_KEY = "dMnqMMZMUnN5YpvKENaEhdQQ5jxDqddt"
    API_USERAGENT = "pyLoad-B1RS5N"
    API_URL = "https://api.fshare.vn/api/"

    # See https://www.fshare.vn/api-doc
    def api_request(self, method, session_id=None, **kwargs):
        self.req.http.c.setopt(pycurl.USERAGENT, self.API_USERAGENT)

        if len(kwargs) == 0:
            json_data = self.load(
                self.API_URL + method,
                cookies=[("fshare.vn", "session_id", session_id)]
                if session_id
                else True,
            )

        else:
            self.req.http.c.setopt(
                pycurl.HTTPHEADER, ["Content-Type: application/json"]
            )
            json_data = self.load(
                self.API_URL + method,
                post=json.dumps(kwargs),
                cookies=[("fshare.vn", "session_id", session_id)]
                if session_id
                else True,
            )

        return json.loads(json_data)

    def grab_info(self, user, password, data):
        trafficleft = None
        premium = False

        api_data = self.api_request("user/get", session_id=data["session_id"])

        expire_vip = api_data.get("expire_vip", "")
        validuntil = float(expire_vip) if expire_vip.isnumeric() else None

        if validuntil:
            premium = True

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        user = user.lower()

        fshare_session_cache = self.db.retrieve("fshare_session_cache") or {}
        if user in fshare_session_cache:
            data["token"] = fshare_session_cache[user]["token"]
            data["session_id"] = fshare_session_cache[user]["session_id"]

            try:
                api_data = self.api_request("user/get", session_id=data["session_id"])

            except BadHeader as exc:
                if exc.code == 401:
                    del fshare_session_cache[user]
                    self.db.store("fshare_session_cache", fshare_session_cache)

            if api_data.get("email", "").lower() == user:
                self.skip_login()

            else:
                del fshare_session_cache[user]
                self.db.store("fshare_session_cache", fshare_session_cache)

        data["token"] = None
        data["session_id"] = None

        try:
            api_data = self.api_request(
                "user/login", app_key=self.API_KEY, user_email=user, password=password
            )
        except BadHeader as exc:
            self.log_error(self._("Login failed, error code {}").format(exc.code))
            self.fail_login()

        if api_data["code"] != 200:
            self.log_error(api_data["msg"])
            self.fail_login()

        fshare_session_cache[user] = {
            "token": api_data["token"],
            "session_id": api_data["session_id"],
        }
        self.db.store("fshare_session_cache", fshare_session_cache)

        data["token"] = fshare_session_cache[user]["token"]
        data["session_id"] = fshare_session_cache[user]["session_id"]
