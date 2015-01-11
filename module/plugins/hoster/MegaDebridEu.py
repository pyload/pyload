# -*- coding: utf-8 -*-

import re

from urllib import unquote_plus

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class MegaDebridEu(MultiHoster):
    __name__    = "MegaDebridEu"
    __type__    = "hoster"
    __version__ = "0.46"

    __pattern__ = r'http://((?:www\d+\.|s\d+\.)?mega-debrid\.eu|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/download/file/[\w^_]+'

    __description__ = """mega-debrid.eu multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("D.Ducatel", "dducatel@je-geek.fr")]


    API_URL = "https://www.mega-debrid.eu/api.php"


    def getFilename(self, url):
        try:
            return unquote_plus(url.rsplit("/", 1)[1])
        except IndexError:
            return ""


    def handlePremium(self, pyfile):
        if not self.api_load():
            self.exitOnFail("Unable to connect to Mega-debrid.eu")

        self.link = self.debridLink(pyfile.url)
        self.logDebug("New URL: " + self.link)

        filename = self.getFilename(self.link)
        if filename != "":
            pyfile.name = filename


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


    def debridLink(self, linkToDebrid):
        """
        Debrid a link
        Return The debrided link if succeed or original link if fail
        """
        jsonResponse = self.load(self.API_URL, get={'action': 'getLink', 'token': self.token},
                                 post={"link": linkToDebrid})
        res = json_loads(jsonResponse)

        if res['response_code'] == "ok":
            debridedLink = res['debridLink'][1:-1]
            return debridedLink
        else:
            self.exitOnFail("Unable to debrid %s" % linkToDebrid)


    def exitOnFail(self, msg):
        """
        exit the plugin on fail case
        And display the reason of this failure
        """
        if self.getConfig("unloadFailing"):
            self.logError(_(msg))
            self.resetAccount()
        else:
            self.fail(_(msg))


getInfo = create_getInfo(MegaDebridEu)
