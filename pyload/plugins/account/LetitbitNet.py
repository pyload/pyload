# -*- coding: utf-8 -*-

from pyload.plugins.Account import Account
# from pyload.utils import json_loads, json_dumps


class LetitbitNet(Account):
    __name    = "LetitbitNet"
    __type    = "account"
    __version = "0.01"

    __description = """Letitbit.net account plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    def loadAccountInfo(self, user, req):
        ## DISABLED BECAUSE IT GET 'key exausted' EVEN IF VALID ##
        # api_key = self.accounts[user]['password']
        # json_data = [api_key, ['key/info']]
        # api_rep = req.load('http://api.letitbit.net/json', post={'r': json_dumps(json_data)})
        # self.logDebug("API Key Info: " + api_rep)
        # api_rep = json_loads(api_rep)
        #
        # if api_rep['status'] == 'FAIL':
        #     self.logWarning(api_rep['data'])
        #     return {'valid': False, 'premium': False}

        return {"premium": True}


    def login(self, user, data, req):
        # API_KEY is the username and the PREMIUM_KEY is the password
        self.logInfo(_("You must use your API KEY as username and the PREMIUM KEY as password"))
