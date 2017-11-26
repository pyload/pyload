# -*- coding: utf-8 -*-
import time

from ..internal.MultiAccount import MultiAccount
from ..internal.misc import json


class LeechThreeHundreedSixtyCom(MultiAccount):
    __name__ = "LeechThreeHundreedSixtyCom"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __description__ = """Leech360.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    __config__ = [("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
                  ("mh_list", "str", "Hoster list (comma separated)", ""),
                  ("mh_interval", "int", "Reload interval in hours", 12)]

    LOGIN_TIMEOUT = 8 * 60
    TUNE_TIMEOUT = False

    API_URL = "https://leech360.com/api/get_"

    def api_response(self, method, **kwargs):
        if 'pass_' in kwargs:
            kwargs['pass'] = kwargs.pop('pass_')
        json_data = self.load(self.API_URL + method, get=kwargs)
        return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        api_data = self.api_response("support", token=data['token'])
        valid_status = ("online", "vip") if self.info['data']['premium'] else ("online")
        return [_h['hostname'] for _h in api_data['data'].values() if _h['status'] in valid_status]

    def grab_info(self, user, password, data):
        api_data = self.api_response("userinfo", token=data['token'])

        premium_expire = int(api_data['data'].get('premium_expire', 0))
        status = api_data['data']['status']

        if status == "lifetime":
            premium = True
            validuntil = -1

        elif premium_expire > 0:
            premium = True
            validuntil = float(premium_expire)

        else:
            premium = False
            validuntil = time.mktime(time.strptime(status, "%b d %Y %I:%M %p"))

        # @TODO: Remove `/ 1024` in 0.4.10
        trafficleft = (536870912000l - int(api_data['data'].get('total_used', 0))) / 1024
        return {'premium': premium,
                'validuntil': validuntil ,
                'trafficleft': trafficleft}

    def signin(self, user, password, data):
        api_data = self.api_response("token", user=user, pass_=password)
        if api_data['error']:
            self.log_warning(api_data['error_message'])
            self.fail_login()

        data['token'] = api_data['token']


