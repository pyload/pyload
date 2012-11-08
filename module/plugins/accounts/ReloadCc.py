from module.plugins.Account   import Account

from module.common.json_layer import json_loads

class ReloadCc(Account):
    __name__ = "ReloadCc"
    __version__ = "0.1"
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
        
        # Check if user and password are valid
        if status['status'] != "ok":
            self.wrongPassword()

    
    def getAccountStatus(self, user, req):
        pwd = "pwd=%s" % self.accounts[user]['password']

        try:
            pwd = "hash=%s" % self.accounts[user]['pwdhash']
        except Exception:
            pass

        # Use reload.cc API v1 to retrieve account info and return the parsed json answer
        answer = req.load("https://api.reload.cc/login?via=pyload&v=1&get_traffic=true&user=%s&%s" % (user, pwd))            
        return json_loads(answer)