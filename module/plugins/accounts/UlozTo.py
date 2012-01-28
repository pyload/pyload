# -*- coding: utf-8 -*-

from module.plugins.Account import Account
import re

class UlozTo(Account):
    __name__ = "UlozTo"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """uloz.to account plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    TRAFFIC_LEFT_PATTERN = r'<li class="credit"><a href="/kredit/" class="coins" title="[^"]* GB = ([^"]+) MB">'

    def loadAccountInfo(self, user, req):
        html = req.load("http://www.uloz.to/statistiky/", decode = True)
                    
        found = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        trafficleft = int(float(found.group(1).replace(' ','').replace(',','.')) * 1000 / 1.024) if found else 0
        self.premium = True if trafficleft else False 
        
        return {"validuntil": -1, "trafficleft": trafficleft}
    
    def login(self, user, data, req):
        html = req.load('http://www.uloz.to/?do=authForm-submit', post = {
            "login": "Přihlásit",
            "password": data['password'],
            "trvale": "on",
            "username":	user
            }, decode = True)
        
        if '<ul class="error">' in html:
            self.wrongPassword()