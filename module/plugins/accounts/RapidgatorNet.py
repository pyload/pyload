# -*- coding: utf-8 -*-

from module.plugins.internal.Account import Account
from module.common.json_layer import json_loads


class RapidgatorNet(Account):
    __name__    = "RapidgatorNet"
    __type__    = "account"
    __version__ = "0.11"

    __description__ = """Rapidgator.net account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    API_URL = "http://rapidgator.net/api/user"


    def load_account_info(self, user, req):
        validuntil  = None
        trafficleft = None
        premium     = False
        sid         = None

        try:
            sid = self.get_account_data(user).get('sid', None)
            assert sid

            html = self.load("%s/info" % self.API_URL, get={'sid': sid}, req=req)

            self.log_debug("API:USERINFO", html)

            json = json_loads(html)

            if json['response_status'] == 200:
                if "reset_in" in json['response']:
                    self.schedule_refresh(user, json['response']['reset_in'])

                validuntil  = json['response']['expire_date']
                trafficleft = float(json['response']['traffic_left']) / 1024  #@TODO: Remove `/ 1024` in 0.4.10
                premium     = True
            else:
                self.log_error(json['response_details'])

        except Exception, e:
            self.log_error(e)

        return {'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'premium'    : premium,
                'sid'        : sid}


    def login(self, user, data, req):
        try:
            html = self.load('%s/login' % self.API_URL, post={"username": user, "password": data['password']}, req=req)

            self.log_debug("API:LOGIN", html)

            json = json_loads(html)

            if json['response_status'] == 200:
                data['sid'] = str(json['response']['session_id'])
                return
            else:
                self.log_error(json['response_details'])

        except Exception, e:
            self.log_error(e)

        self.wrong_password()
