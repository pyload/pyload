# -*- coding: utf-8 -*-

import re
import urllib

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class FastixRu(MultiHoster):
    __name__    = "FastixRu"
    __type__    = "hoster"
    __version__ = "0.13"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?fastix\.(ru|it)/file/\w{24}'
    __config__  = [("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Fastix multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Massimo Rosamilia", "max@spiritix.eu")]


    def setup(self):
        self.chunk_limit = 3


    def handle_premium(self, pyfile):
        api_key = self.account.get_data(self.user)
        api_key = api_key['api']

        self.html = self.load("http://fastix.ru/api_v2/",
                         get={'apikey': api_key, 'sub': "getdirectlink", 'link': pyfile.url})

        data = json_loads(self.html)

        self.log_debug("Json data", data)

        if "error\":true" in self.html:
            self.offline()
        else:
            self.link = data['downloadlink']


getInfo = create_getInfo(FastixRu)
