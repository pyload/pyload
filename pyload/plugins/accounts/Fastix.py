from module.plugins.Account import Account

class Fastix(Account):
    __name__ = "Fastix"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """Fastix account plugin"""
    __author_name__ = ("Massimo, Rosamilia")
    __author_mail__ = ("max@spiritix.eu")

    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        page = req.load("http://fastix.ru/api_v2/?apikey=%s&sub=getaccountdetails" % (data["api"]))
        points = page.split('"points":')
        points = points[1]
        points = points.split(',')
        points = points[0]
        kb = float(points)
        kb = kb/1000
        kb = kb*1024*1024
        if points > 0:
            account_info = {"validuntil": -1, "trafficleft": kb}
        else:
            account_info = {"validuntil": None, "trafficleft": None, "premium": False}
        return account_info


    def login(self, user, data, req):      
        page = req.load("http://fastix.ru/api_v2/?sub=get_apikey&email=%s&password=%s" % (user, data["password"]))
        api = page.split('apikey":"')
        api = api[1]
        api = api.split('"')
        api = api[0]
        data["api"] = api
        out_file = open("fastix_api.txt","w")
        out_file.write(api)
        out_file.close()
        if "error_code" in page:
            self.wrongPassword()
            