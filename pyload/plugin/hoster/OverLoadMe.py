# -*- coding: utf-8 -*-

import re

from random import randrange
from urllib import unquote

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHoster import MultiHoster
from pyload.utils import parseFileSize


class OverLoadMe(MultiHoster):
    __name__    = "OverLoadMe"
    __type__    = "hoster"
    __version__ = "0.11"

    __pattern__ = r'https?://.*overload\.me/.+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Over-Load.me multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("marley", "marley@over-load.me")]


    def setup(self):
        self.chunkLimit = 5


    def handlePremium(self, pyfile):
        https = "https" if self.getConfig('ssl') else "http"
        data  = self.account.getAccountData(self.user)
        page  = self.load(https + "://api.over-load.me/getdownload.php",
                          get={'auth': data['password'],
                               'link': pyfile.url})

        data = json_loads(page)

        self.logDebug(data)

        if data['error'] == 1:
            self.logWarning(data['msg'])
            self.tempOffline()
        else:
            if pyfile.name and pyfile.name.endswith('.tmp') and data['filename']:
                pyfile.name = data['filename']
                pyfile.size = parseFileSize(data['filesize'])

            http_repl = ["http://", "https://"]
            self.link = data['downloadlink'].replace(*http_repl if self.getConfig('ssl') else http_repl[::-1])


