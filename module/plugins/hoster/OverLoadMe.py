# -*- coding: utf-8 -*-

import re
import urllib

from module.plugins.internal.MultiHoster import MultiHoster
from module.plugins.internal.misc import json, parse_size


class OverLoadMe(MultiHoster):
    __name__    = "OverLoadMe"
    __type__    = "hoster"
    __version__ = "0.18"
    __status__  = "testing"

    __pattern__ = r'https?://.*overload\.me/.+'
    __config__  = [("activated"   , "bool", "Activated"                                        , True ),
                   ("use_premium" , "bool", "Use premium account if available"                 , True ),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , False),
                   ("chk_filesize", "bool", "Check file size"                                  , True ),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10   ),
                   ("revertfailed", "bool", "Revert to standard download if fails"             , True )]

    __description__ = """Over-Load.me multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("marley", "marley@over-load.me")]


    def setup(self):
        self.chunk_limit = 5


    def handle_premium(self, pyfile):
        data  = self.account.get_data()
        page  = self.load("https://api.over-load.me/getdownload.php",
                          get={'auth': data['password'],
                               'link': pyfile.url})

        data = json.loads(page)

        self.log_debug(data)

        if data['error'] == 1:
            self.log_warning(data['msg'])
            self.temp_offline()
        else:
            self.link = data['downloadlink']
            if pyfile.name and pyfile.name.endswith('.tmp') and data['filename']:
                pyfile.name = data['filename']
                pyfile.size = parse_size(data['filesize'])
