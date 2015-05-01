# -*- coding: utf-8 -*-

import re
import urllib

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHoster import MultiHoster
from pyload.utils import parseFileSize


class AlldebridCom(MultiHoster):
    __name    = "AlldebridCom"
    __type    = "hoster"
    __version = "0.46"

    __pattern = r'https?://(?:www\.|s\d+\.)?alldebrid\.com/dl/[\w^_]+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Alldebrid.com multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Andy Voigt", "spamsales@online.de")]


    def setup(self):
        self.chunkLimit = 16


    def handlePremium(self, pyfile):
        password = self.getPassword()

        data = json_loads(self.load("http://www.alldebrid.com/service.php",
                                     get={'link': pyfile.url, 'json': "true", 'pw': password}))

        self.logDebug("Json data", data)

        if data['error']:
            if data['error'] == "This link isn't available on the hoster website.":
                self.offline()
            else:
                self.logWarning(data['error'])
                self.tempOffline()
        else:
            if pyfile.name and not pyfile.name.endswith('.tmp'):
                pyfile.name = data['filename']
            pyfile.size = parseFileSize(data['filesize'])
            self.link = data['link']

        if self.getConfig('ssl'):
            self.link = self.link.replace("http://", "https://")
        else:
            self.link = self.link.replace("https://", "http://")
