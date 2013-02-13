from module.plugins.Account   import Account

from module.common.json_layer import json_loads

from module.network.HTTPRequest import BadHeader

class ReloadCc(Account):
    __name__ = "ReloadCc"
    __version__ = "0.3"
    __type__ = "account"
    __description__ = """Reload.Cc account plugin"""

    __author_name__ = ("Reload Team")
    __author_mail__ = ("hello@reload.cc")

    def loadAccountInfo(self, user, req):

        # Get user data from reload.cc
        status = self.getAccountStatus(user, req)

        # Parse account info
        account_info = {"validuntil": float(status['msg']['expires']),
                        "pwdhash": status['msg']['hash'],
                        "trafficleft": -1}

        return account_info

    def login(self, user, data, req):

        # Get user data from reload.cc
        status = self.getAccountStatus(user, req)

        if not status:
            raise Exception("There was an error upon logging in to Reload.cc!")

        # Check if user and password are valid
        if status['status'] != "ok":
            self.wrongPassword()


    def getAccountStatus(self, user, req):
        # Use reload.cc API v1 to retrieve account info and return the parsed json answer
        query_params = dict(
            via='pyload',
            v=1,
            get_traffic='true',
            user=user
        )

        try:
            query_params.update(dict(hash=self.infos[user]['pwdhash']))
        except Exception:
            query_params.update(dict(pwd=self.accounts[user]['password']))

        try:
            answer = req.load("http://api.reload.cc/login", get=query_params)
        except BadHeader, e:
            if e.code == 400:
                raise Exception("There was an unknown error within the Reload.cc plugin.")
            elif e.code == 401:
                self.wrongPassword()
            elif e.code == 402:
                self.expired(user)
            elif e.code == 403:
                raise Exception("Your account is disabled. Please contact the Reload.cc support!")
            elif e.code == 409:
                self.empty(user)
            elif e.code == 503:
                self.logInfo("Reload.cc is currently in maintenance mode! Please check again later.")
                self.wrongPassword()
            return None

        return json_loads(answer)
