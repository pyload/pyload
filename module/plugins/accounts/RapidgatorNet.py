# -*- coding: utf-8 -*-

from module.plugins.Account import Account
from module.common.json_layer import json_loads


class RapidgatorNet(Account):
    __name__ = "RapidgatorNet"
    __type__ = "account"
    __version__ = "0.04"

    __description__ = """Rapidgator.net account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    API_URL = 'http://rapidgator.net/api/user'


    def loadAccountInfo(self, user, req):
        try:
            sid = self.getAccountData(user).get('SID')
            assert sid

            json = req.load("%s/info?sid=%s" % (self.API_URL, sid))
            self.logDebug("API:USERINFO", json)
            json = json_loads(json)

            if json['response_status'] == 200:
                if "reset_in" in json['response']:
                    self.scheduleRefresh(user, json['response']['reset_in'])

                return {"validuntil": json['response']['expire_date'],
                        "trafficleft": int(json['response']['traffic_left']) / 1024,
                        "premium": True}
            else:
                self.logError(json['response_details'])
        except Exception, e:
            self.logError(e)

        return {"validuntil": None, "trafficleft": None, "premium": False}

    def login(self, user, data, req):
        try:
            json = req.load('%s/login' % self.API_URL, post={"username": user, "password": data['password']})
            self.logDebug("API:LOGIN", json)
            json = json_loads(json)

            if json['response_status'] == 200:
                data['SID'] = str(json['response']['session_id'])
                return
            else:
                self.logError(json['response_details'])
        except Exception, e:
            self.logError(e)

        self.wrongPassword()
