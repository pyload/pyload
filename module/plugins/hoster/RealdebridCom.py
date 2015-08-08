# -*- coding: utf-8 -*-

import re
import time
import urllib

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo
from module.utils import parseFileSize as parse_size


class RealdebridCom(MultiHoster):
    __name__    = "RealdebridCom"
    __type__    = "hoster"
    __version__ = "0.69"
    __status__  = "testing"

    __pattern__ = r'https?://((?:www\.|s\d+\.)?real-debrid\.com/dl/|[\w^_]\.rdb\.so/d/)[\w^_]+'
    __config__  = [("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Real-Debrid.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Devirex Hazzard", "naibaf_11@yahoo.de")]


    def setup(self):
        self.chunk_limit = 3


    def handle_premium(self, pyfile):
        data = json_loads(self.load("https://real-debrid.com/ajax/unrestrict.php",
                                    get={'lang'    : "en",
                                         'link'    : pyfile.url,
                                         'password': self.get_password(),
                                         'time'    : int(time.time() * 1000)}))

        self.log_debug("Returned Data: %s" % data)

        if data['error'] != 0:
            if data['message'] == "Your file is unavailable on the hoster.":
                self.offline()
            else:
                self.log_warning(data['message'])
                self.temp_offline()
        else:
            if pyfile.name and pyfile.name.endswith('.tmp') and data['file_name']:
                pyfile.name = data['file_name']
            pyfile.size = parse_size(data['file_size'])
            self.link = data['generated_links'][0][-1]


getInfo = create_getInfo(RealdebridCom)
