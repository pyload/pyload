# -*- coding: utf-8 -*-

import re
import urllib

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class MegaDebridEu(MultiHoster):
    __name__    = "MegaDebridEu"
    __type__    = "hoster"
    __version__ = "0.50"
    __status__  = "testing"

    __pattern__ = r'http://((?:www\d+\.|s\d+\.)?mega-debrid\.eu|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/download/file/[\w^_]+'
    __config__  = [("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Mega-debrid.eu multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("D.Ducatel", "dducatel@je-geek.fr")]


    API_URL = "https://www.mega-debrid.eu/api.php"


    def api_load(self):
        """
        Connexion to the mega-debrid API
        Return True if succeed
        """
        user, info = self.account.select()
        jsonResponse = self.load(self.API_URL,
                                 get={'action': 'connectUser', 'login': user, 'password': info['login']['password']})
        res = json_loads(jsonResponse)

        if res['response_code'] == "ok":
            self.token = res['token']
            return True
        else:
            return False


    def handle_premium(self, pyfile):
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


getInfo = create_getInfo(MegaDebridEu)
