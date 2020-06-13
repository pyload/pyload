# -*- coding: utf-8 -*-

import time

import pycurl
from module.network.HTTPRequest import BadHeader

from ..internal.misc import json
from ..internal.MultiAccount import MultiAccount


class DownsterNet(MultiAccount):
    __name__ = "DownsterNet"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    __description__ = """Downster.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [(None, None)]

    API_URL = "https://downster.net/api/"

    def api_response(self, method, get={}, **kwargs):
        try:
            res = self.load(self.API_URL + method,
                            get=get,
                            post=json.dumps(kwargs))
        except BadHeader, e:
            res = e.content

        res = json.loads(res)

        return res

    def grab_hosters(self, user, password, data):
        api_data = self.api_response("download/usage")
        if not api_data['success']:
            self.log_error('Could not get hoster info: ' + api_data['error'])
            return []

        else:
            return [hoster['hoster'] for hoster in api_data['data']]

    def grab_info(self, email, password, data):
        api_data = self.api_response("user/info")

        if not api_data['success']:
            info = {'validuntil': None,
                    'trafficleft': None,
                    'premium': False}

            self.log_error('Could not get user info: ' + api_data['error'])

        else:
            #: Parse account info
            info = {'validuntil': float(api_data['data']['premiumUntil']),
                    'trafficleft': -1}

            info['premium'] = info['validuntil'] > time.time()

        return info

    def signin(self, user, password, data):
        try:
            api_data = self.api_response("user/authenticate",
                                         email=user,
                                         password=password)

        except BadHeader, e:
            self.log_error(e.content)
            self.fail_login()

        if not api_data['success']:
            self.fail_login(api_data['error'])
