# -*- coding: utf-8 -*-

import re

from urllib import unquote_plus

from pyload.utils import json_loads
from pyload.plugins.Hoster import Hoster


class MegaDebridEu(Hoster):
    __name    = "MegaDebridEu"
    __type    = "hoster"
    __version = "0.40"

    __pattern = r'^https?://(?:w{3}\d+\.mega-debrid\.eu|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/download/file/[^/]+/.+$'

    __description = """mega-debrid.eu hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("D.Ducatel", "dducatel@je-geek.fr")]


    API_URL = "https://www.mega-debrid.eu/api.php"


    def getFilename(self, url):
        try:
            return unquote_plus(url.rsplit("/", 1)[1])
        except IndexError:
            return ""


    def process(self, pyfile):
        if re.match(self.__pattern, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.exitOnFail("Please enter your %s account or deactivate this plugin" % "Mega-debrid.eu")
        else:
            if not self.connectToApi():
                self.exitOnFail("Unable to connect to Mega-debrid.eu")

            self.logDebug("Old URL: %s" % pyfile.url)
            new_url = self.debridLink(pyfile.url)
            self.logDebug("New URL: " + new_url)

        filename = self.getFilename(new_url)
        if filename != "":
            pyfile.name = filename
        self.download(new_url, disposition=True)


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
