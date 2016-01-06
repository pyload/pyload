# -*- coding: utf-8 -*-

import re
import urllib

from module.plugins.internal.MultiHoster import MultiHoster
from module.plugins.internal.misc import json, parse_size


class AlldebridCom(MultiHoster):
    __name__    = "AlldebridCom"
    __type__    = "hoster"
    __version__ = "0.51"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.|s\d+\.)?alldebrid\.com/dl/[\w^_]+'
    __config__  = [("activated"   , "bool", "Activated"                                        , True ),
                   ("use_premium" , "bool", "Use premium account if available"                 , True ),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , False),
                   ("chk_filesize", "bool", "Check file size"                                  , True ),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10   ),
                   ("revertfailed", "bool", "Revert to standard download if fails"             , True )]

    __description__ = """Alldebrid.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Andy Voigt", "spamsales@online.de")]


    def setup(self):
        self.chunk_limit = 16


    def handle_premium(self, pyfile):
        password = self.get_password()

        html = self.load("http://www.alldebrid.com/service.php",
                         get={'link': pyfile.url, 'json': "true", 'pw': password})
        data = json.loads(html)

        self.log_debug("Json data", data)

        if data['error']:
            if data['error'] == "This link isn't available on the hoster website.":
                self.offline()
            else:
                self.log_warning(data['error'])
                self.temp_offline()
        else:
            if pyfile.name and not pyfile.name.endswith('.tmp'):
                pyfile.name = data['filename']
            pyfile.size = parse_size(data['filesize'])
            self.link = data['link']
