# -*- coding: utf-8 -*-

import time
import re
import pycurl

from module.network.HTTPRequest import BadHeader

from ..internal.misc import json
from ..internal.MultiAccount import MultiAccount


def args(**kwargs):
    return kwargs


class RealdebridCom(MultiAccount):
    __name__ = "RealdebridCom"
    __type__ = "account"
    __version__ = "0.57"
    __status__ = "testing"

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    __description__ = """Real-Debrid.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Devirex Hazzard", "naibaf_11@yahoo.de"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
                   ("Synology PAT", "pat@synology.com")]

    LOGIN_URL = "https://real-debrid.com/ajax/login.php"
    API_TOKEN_URL = "https://real-debrid.com/apitoken"
    API_TOKEN_PATTERN = r'querySelectorAll.+private_token.+=\s*\'([0-9A-z]+)\''
    API_URL = "https://api.real-debrid.com/rest/1.0"

    def api_response(self, namespace, get={}, post={}):
        json_data = self.load(self.API_URL + namespace, get=get, post=post)

        return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        hosters = self.api_response("/hosts/domains")
        return hosters

    def grab_info(self, user, password, data):
        account = self.api_response("/user", args(auth_token=data['auth_token']))

        validuntil = time.time() + account["premium"]

        return {'validuntil': validuntil,
                'trafficleft': -1,
                'premium': True if account["premium"] > 0 else False}

    def signin(self, user, password, data):
        self._signin(user, password, data)

        html = self.load(self.API_TOKEN_URL)
        matched = re.search(self.API_TOKEN_PATTERN, html)
        if matched is None:
            self.fail_login('No api-token been found in response.')

        data['auth_token'] = matched.group(1)

        try:
            account = self.api_response("/user", args(auth_token=data['auth_token']))

        except BadHeader, e:
            if e.code == 401:
                self.log_error(_("Password for Real-debrid should be the API token - get it from: https://real-debrid.com/apitoken"))
                self.fail_login()

            else:
                raise

        if user != account["username"]:
            self.fail_login()

    def _signin(self, user, password, data):
        """ Sign in by username and password.

        This will get cookie "auth". That makes request for api-token valid.
        """

        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        self.load(self.LOGIN_URL, {
            'user': user,
            'pass': password,
            'pin_challenge': '',
            'pin_answer': "PIN: 000000",
            'time': time.time()
        })
