# -*- coding: utf-8 -*-

import time
import pycurl

from ..internal.misc import json
from ..internal.MultiAccount import MultiAccount
from ...network.HTTPRequest import BadHeader


class DownsterNet(MultiAccount):
    __name__ = "DownsterNet"
    __type__ = "account"
    __version__ = "0.1"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12)
    ]

    __description__ = """Downster.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [(None, None)]

    def grab_hosters(self, user, password, data):
        return self.get_data('hosters')

    def grab_info(self, email, password, data):
        user_info = json.loads(self.load("https://downster.net/api/user/info"))
        usage = json.loads(self.load("https://downster.net/api/download/usage"))

        if not user_info['success']:
            info = {'validuntil': None,
                    'trafficleft': None,
                    'premium': False}

            self.log_error('Could not get user info: ' + user_info['error'])
        else:
            #: Parse account info
            info = {'validuntil': float(user_info['data']['premiumUntil']),
                    'trafficleft': -1}

            info['premium'] = info['validuntil'] > time.time()

            if not usage['success']:
                info['hosters'] = []
                self.log_error('Could not get hoster info: ' + usage['error'])
            else:
                info['hosters'] = [hoster['hoster'] for hoster in usage['data']]

        return info

    def api_response(self, url, post_data):
        self.req.http.c.setopt(pycurl.HTTPHEADER, [
            "Accept: application/json, text/plain, */*",
            "Content-Type: application/json"
        ])

        try:
            res = json.loads(self.load(url, post=json.dumps(post_data)))
        except (BadHeader, ValueError) as e:
            self.log_error(e.message)
            self.fail(e.message)

        # Headers back to normal
        self.req.http.c.setopt(pycurl.HTTPHEADER, [
            "Accept: */*",
            "Accept-Language: en-US,en",
            "Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7",
            "Connection: keep-alive",
            "Keep-Alive: 300",
            "Expect:"
        ])

        return res

    def signin(self, email, password, data):
        payload = self.api_response("https://downster.net/api/user/authenticate", {'email': email, 'password': password})

        if not payload['success']:
            self.fail_login(payload['error'])
            return
