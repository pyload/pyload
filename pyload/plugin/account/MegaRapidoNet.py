# -*- coding: utf-8 -*-

import re
import time

from pyload.plugin.Account import Account


class MegaRapidoNet(Account):
    __name    = "MegaRapidoNet"
    __type    = "account"
    __version = "0.02"

    __description = """MegaRapido.net account plugin"""
    __license     = "GPLv3"
    __authors     = [("Kagenoshin", "kagenoshin@gmx.ch")]


    VALID_UNTIL_PATTERN = r'<\s*?div[^>]*?class\s*?=\s*?[\'"]premium_index[\'"].*?>[^<]*?<[^>]*?b.*?>\s*?TEMPO\s*?PREMIUM.*?<[^>]*?/b.*?>\s*?(\d*)[^\d]*?DIAS[^\d]*?(\d*)[^\d]*?HORAS[^\d]*?(\d*)[^\d]*?MINUTOS[^\d]*?(\d*)[^\d]*?SEGUNDOS'
    USER_ID_PATTERN     = r'<\s*?div[^>]*?class\s*?=\s*?["\']checkbox_compartilhar["\'].*?>.*?<\s*?input[^>]*?name\s*?=\s*?["\']usar["\'].*?>.*?<\s*?input[^>]*?name\s*?=\s*?["\']user["\'][^>]*?value\s*?=\s*?["\'](.*?)\s*?["\']'


    def loadAccountInfo(self, user, req):
        validuntil  = None
        trafficleft = None
        premium     = False

        html = req.load("http://megarapido.net/gerador", decode=True)

        validuntil = re.search(self.VALID_UNTIL_PATTERN, html)
        if validuntil:
            #hier weitermachen!!! (müssen umbedingt die zeit richtig machen damit! (sollte aber möglich))
            validuntil  = time.time() + int(validuntil.group(1)) * 24 * 3600 + int(validuntil.group(2)) * 3600 + int(validuntil.group(3)) * 60 + int(validuntil.group(4))
            trafficleft = -1
            premium     = True

        return {'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'premium'    : premium}


    def login(self, user, data, req):
        req.load("http://megarapido.net/login")
        req.load("http://megarapido.net/painel_user/ajax/logar.php",
                 post={'login': user, 'senha': data['password']},
                 decode=True)

        html = req.load("http://megarapido.net/gerador")

        if "sair" not in html.lower():
            self.wrongPassword()
        else:
            m = re.search(self.USER_ID_PATTERN, html)
            if m:
                data['uid'] = m.group(1)
            else:
                self.fail("Couldn't find the user ID")
