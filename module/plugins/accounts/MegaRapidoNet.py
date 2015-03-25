# -*- coding: utf-8 -*-
import re
from time import mktime, strptime, time

from module.plugins.Account import Account


class MegaRapidoNet(Account):
    __name__ = "MegaRapidoNet"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = """Megarapido.net account plugin"""
    __author_name__ = ("Kagenoshin")
    __author_mail__ = ("kagenoshin@gmx.ch")

    VALIDUNTIL_PATTERN = re.compile(r'<\s*?div[^>]*?class\s*?=\s*?[\'"]premium_index[\'"][^>]*>[^<]*?<[^>]*?b[^>]*>\s*?TEMPO\s*?PREMIUM[^<]*<[^>]*?/b[^>]*>\s*?(\d*)[^\d]*?DIAS[^\d]*?(\d*)[^\d]*?HORAS[^\d]*?(\d*)[^\d]*?MINUTOS[^\d]*?(\d*)[^\d]*?SEGUNDOS', re.I)
    USER_ID_PATTERN= re.compile(r' <\s*?div[^>]*?class\s*?=\s*?["\']checkbox_compartilhar["\'][^>]*>[^<]*<\s*?input[^>]*?name\s*?=\s*?["\']usar["\'][^>]*>[^<]*<\s*?input[^>]*?name\s*?=\s*?["\']user["\'][^>]*?value\s*?=\s*?["\'](.*?)\s*?["\']', re.I)

    def loadAccountInfo(self, user, req):
        response = req.load("http://megarapido.net/gerador", decode=True)

        validuntil = self.VALIDUNTIL_PATTERN.search(response)
        if validuntil:
            #hier weitermachen!!! (müssen umbedingt die zeit richtig machen damit! (sollte aber möglich))
            validuntil = time() + int(validuntil.group(1))*24*3600 + int(validuntil.group(2))*3600 + int(validuntil.group(3))*60 + int(validuntil.group(4))

        if validuntil:
            return {"trafficleft": -1, "validuntil": validuntil}
        else:
            return {"premium": False}

    def login(self, user, data, req):
        self.loginname = user
        self.password = data["password"]
        post_data = {'login': self.loginname, 'senha': self.password}
        req.load("http://megarapido.net/login")
        response = req.load("http://megarapido.net/painel_user/ajax/logar.php", post=post_data, decode=True)
        response = req.load("http://megarapido.net/gerador")
        if 'sair' not in response.lower():
            self.wrongPassword()
        else:
        	user_id = self.USER_ID_PATTERN.search(response)
        	if user_id:
        		user_id = user_id.group(1)
        		self.setStorage("MegarapidoNet_userID", user_id)
        	else:
        		self.fail("Couldn't find the user ID")