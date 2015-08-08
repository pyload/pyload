# -*- coding: utf-8 -*-

import re
import urllib

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo
from module.utils import parseFileSize as parse_size


class AlldebridCom(MultiHoster):
    __name__    = "AlldebridCom"
    __type__    = "hoster"
    __version__ = "0.48"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.|s\d+\.)?alldebrid\.com/dl/[\w^_]+'
    __config__  = [("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Alldebrid.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Andy Voigt", "spamsales@online.de")]


    def setup(self):
        self.chunk_limit = 16


    def handle_premium(self, pyfile):
        password = self.get_password()

        data = json_loads(self.load("http://www.alldebrid.com/service.php",
                                     get={'link': pyfile.url, 'json': "true", 'pw': password}))

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


getInfo = create_getInfo(AlldebridCom)
