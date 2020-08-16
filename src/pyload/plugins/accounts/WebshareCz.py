# -*- coding: utf-8 -*-
import hashlib
import re
import time

from pyload.core.network.request_factory import get_url

from ..base.account import BaseAccount


class WebshareCz(BaseAccount):
    __name__ = "WebshareCz"
    __type__ = "account"
    __version__ = "0.16"
    __status__ = "testing"

    __description__ = """Webshare.cz account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("rush", "radek.senfeld@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    VALID_UNTIL_PATTERN = r"<vip_until>(.*)</vip_until>"

    TRAFFIC_LEFT_PATTERN = r"<bytes>(.+?)</bytes>"

    API_URL = "https://webshare.cz/api/"

    @classmethod
    def api_response(cls, method, **kwargs):
        return get_url(cls.API_URL + method + "/", post=kwargs)

    def grab_info(self, user, password, data):
        user_data = self.api_response("user_data", wst=data["wst"])

        expiredate = re.search(self.VALID_UNTIL_PATTERN, user_data).group(1)
        if expiredate:
            validuntil = time.mktime(time.strptime(expiredate, "%Y-%m-%d %H:%M:%S"))
            premium = validuntil > time.time()

        else:
            validuntil = -1
            premium = False

        # trafficleft = self.parse_traffic(re.search(self.TRAFFIC_LEFT_PATTERN, user_data).group(1))

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def signin(self, user, password, data):
        salt = self.api_response("salt", username_or_email=user, wst="")

        if "<status>OK</status>" not in salt:
            message = re.search(r"<message>(.+?)</message>", salt).group(1)
            self.log_warning(message)
            self.fail_login()

        salt = re.search("<salt>(.+?)</salt>", salt).group(1)
        salt_pw = salt + password

        password = hashlib.sha1(
            hashlib.md5(salt_pw.encode()).hexdigest().encode()
        ).hexdigest()
        digest = hashlib.md5(user + ":Webshare:" + password).hexdigest()

        login = self.api_response(
            "login",
            digest=digest,
            keep_logged_in=1,
            username_or_email=user,
            password=password,
            wst="",
        )

        if "<status>OK</status>" not in login:
            message = re.search(r"<message>(.+?)</message>", salt).group(1)
            self.log_warning(message)
            self.fail_login()

        data["wst"] = re.search("<token>(.+?)</token>", login).group(1)
