# -*- coding: utf-8 -*-

import re
import urllib

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHoster import MultiHoster


class FastixRu(MultiHoster):
    __name    = "FastixRu"
    __type    = "hoster"
    __version = "0.11"

    __pattern = r'http://(?:www\.)?fastix\.(ru|it)/file/\w{24}'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Fastix multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Massimo Rosamilia", "max@spiritix.eu")]


    def setup(self):
        self.chunkLimit = 3


    def handlePremium(self, pyfile):
        api_key = self.account.getAccountData(self.user)
        api_key = api_key['api']

        self.html = self.load("http://fastix.ru/api_v2/",
                         get={'apikey': api_key, 'sub': "getdirectlink", 'link': pyfile.url})

        data = json_loads(self.html)

        self.logDebug("Json data", data)

        if "error\":true" in self.html:
            self.offline()
        else:
            self.link = data['downloadlink']
