# -*- coding: utf-8 -*-

from module.plugins.internal.Account import Account
# from module.common.json_layer import json_loads, json_dumps


class LetitbitNet(Account):
    __name__    = "LetitbitNet"
    __type__    = "account"
    __version__ = "0.04"
    __status__  = "testing"

    __description__ = """Letitbit.net account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    def parse_info(self, user, password, data, req):
        ## DISABLED BECAUSE IT GET 'key exausted' EVEN IF VALID ##
        # json_data = [password, ['key/info']]
        # api_rep   = self.load("http://api.letitbit.net/json",
        #                       post={'r': json_dumps(json_data)})
        # self.log_debug("API Key Info: " + api_rep)
        # api_rep = json_loads(api_rep)
        #
        # if api_rep['status'] == "FAIL":
        #     self.log_warning(api_rep['data'])
        #     return {'valid': False, 'premium': False}

        return {'premium': True}


    def login(self, user, password, data, req):
        #: API_KEY is the username and the PREMIUM_KEY is the password
        self.log_info(_("You must use your API KEY as username and the PREMIUM KEY as password"))
