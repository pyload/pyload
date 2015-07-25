# -*- coding: utf-8 -*-

import re
import urllib

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo
from module.utils import parseFileSize as parse_size


class OverLoadMe(MultiHoster):
    __name__    = "OverLoadMe"
    __type__    = "hoster"
    __version__ = "0.13"
    __status__  = "testing"

    __pattern__ = r'https?://.*overload\.me/.+'
    __config__  = [("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Over-Load.me multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("marley", "marley@over-load.me")]


    def setup(self):
        self.chunk_limit = 5


    def handle_premium(self, pyfile):
        data  = self.account.get_data(self.user)
        page  = self.load("https://api.over-load.me/getdownload.php",
                          get={'auth': data['password'],
                               'link': pyfile.url})

        data = json_loads(page)

        self.log_debug(data)

        if data['error'] == 1:
            self.log_warning(data['msg'])
            self.temp_offline()
        else:
            self.link = data['downloadlink']
            if pyfile.name and pyfile.name.endswith('.tmp') and data['filename']:
                pyfile.name = data['filename']
                pyfile.size = parse_size(data['filesize'])


getInfo = create_getInfo(OverLoadMe)
