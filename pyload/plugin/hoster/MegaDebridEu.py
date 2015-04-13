# -*- coding: utf-8 -*-

import re

from urllib import unquote_plus

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHoster import MultiHoster


class MegaDebridEu(MultiHoster):
    __name    = "MegaDebridEu"
    __type    = "hoster"
    __version = "0.47"

    __pattern = r'http://((?:www\d+\.|s\d+\.)?mega-debrid\.eu|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/download/file/[\w^_]+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """mega-debrid.eu multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("D.Ducatel", "dducatel@je-geek.fr")]


    API_URL = "https://www.mega-debrid.eu/api.php"


    def api_load(self):
        """
        Connexion to the mega-debrid API
        Return True if succeed
        """
        user, data = self.account.selectAccount()
        jsonResponse = self.load(self.API_URL,
                                 get={'action': 'connectUser', 'login': user, 'password': data['password']})
        res = json_loads(jsonResponse)

        if res['response_code'] == "ok":
            self.token = res['token']
            return True
        else:
            return False


    def handlePremium(self, pyfile):
        """
        Debrid a link
        Return The debrided link if succeed or original link if fail
        """
        if not self.api_load():
            self.error("Unable to connect to remote API")

        jsonResponse = self.load(self.API_URL,
                                 get={'action': 'getLink', 'token': self.token},
                                 post={'link': pyfile.url})

        res = json_loads(jsonResponse)
        if res['response_code'] == "ok":
            self.link = res['debridLink'][1:-1]
