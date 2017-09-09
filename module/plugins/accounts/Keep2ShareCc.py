# -*- coding: utf-8 -*-

from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getURL as get_url

from ..internal.Account import Account
from ..internal.misc import json


class Keep2ShareCc(Account):
    __name__ = "Keep2ShareCc"
    __type__ = "account"
    __version__ = "0.15"
    __status__ = "testing"

    __description__ = """Keep2Share.cc account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("aeronaut", "aeronaut@pianoguy.de"),
                   ("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://keep2share.cc/api/v2/"
    #: See https://github.com/keep2share/api

    @classmethod
    def api_response(cls, method, **kwargs):
        html = get_url(cls.API_URL + method,
                       post=json.dumps(kwargs))
        return json.loads(html)

    def grab_info(self, user, password, data):
        json_data = self.api_response("AccountInfo", auth_token=data['token'])

        return {'validuntil': json_data['account_expires'],
                'trafficleft': json_data['available_traffic'] / 1024,  # @TODO: Remove `/ 1024` in 0.4.10
                'premium': True}

    def signin(self, user, password, data):
        if 'token' in data:
            try:
                json_data = self.api_response("test", auth_token=data['token'])

            except BadHeader, e:
                if e.code == 403:
                    pass

                else:
                    raise
            else:
                self.skip_login()

        try:
            json_data = self.api_response("login", username=user, password=password)

        except BadHeader, e:
            if e.code == 406:
                self.fail_login()

            else:
                raise

        else:
            data['token'] = json_data['auth_token']
