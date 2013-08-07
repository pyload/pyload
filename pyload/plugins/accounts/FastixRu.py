from pyload.plugins.MultiHoster import MultiHoster
from pyload.utils import json_loads


class FastixRu(MultiHoster):
    __name__ = "FastixRu"
    __version__ = "0.02"
    __type__ = "account"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", "False"),
                  ("interval", "int", "Reload interval in hours (0 to disable)", "24")]
    __description__ = """Fastix account plugin"""
    __author_name__ = ("Massimo, Rosamilia")
    __author_mail__ = ("max@spiritix.eu")

    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        page = req.load("http://fastix.ru/api_v2/?apikey=%s&sub=getaccountdetails" % (data["api"]))
        page = json_loads(page)
        points = page['points']
        kb = float(points)
        kb = kb * 1024 ** 2 / 1000
        if points > 0:
            account_info = {"validuntil": -1, "trafficleft": kb}
        else:
            account_info = {"validuntil": None, "trafficleft": None, "premium": False}
        return account_info

    def login(self, user, data, req):
        page = req.load("http://fastix.ru/api_v2/?sub=get_apikey&email=%s&password=%s" % (user, data["password"]))
        api = json_loads(page)
        api = api['apikey']
        data["api"] = api
        if "error_code" in page:
            self.wrongPassword()

    def loadHosterList(self, req):
        page = req.load(
            "http://fastix.ru/api_v2/?apikey=5182964c3f8f9a7f0b00000a_kelmFB4n1IrnCDYuIFn2y&sub=allowed_sources")
        host_list = json_loads(page)
        host_list = host_list['allow']
        return host_list
