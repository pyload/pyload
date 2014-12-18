# -*- coding: utf-8 -*-

import re

from urllib import unquote_plus

from module.common.json_layer import json_loads
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class MegaDebridEu(SimpleHoster):
    __name__    = "MegaDebridEu"
    __type__    = "hoster"
    __version__ = "0.41"

    __pattern__ = r'^https?://(?:w{3}\d+\.mega-debrid\.eu|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/download/file/[^/]+/.+$'

    __description__ = """mega-debrid.eu hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("D.Ducatel", "dducatel@je-geek.fr")]


    MULTI_HOSTER = True

    API_URL = "https://www.mega-debrid.eu/api.php"


    def getFilename(self, url):
        try:
            return unquote_plus(url.rsplit("/", 1)[1])
        except IndexError:
            return ""


    def handleMulti(self):
        if not self.connectToApi():
            self.exitOnFail("Unable to connect to Mega-debrid.eu")

        self.link = self.debridLink(self.pyfile.url)
        self.logDebug("New URL: " + self.link)

        filename = self.getFilename(self.link)
        if filename != "":
            self.pyfile.name = filename


    def connectToApi(self):
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
