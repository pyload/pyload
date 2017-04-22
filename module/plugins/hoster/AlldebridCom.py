# -*- coding: utf-8 -*-

from ..internal.misc import json, parse_size
from ..internal.MultiHoster import MultiHoster


class AlldebridCom(MultiHoster):
    __name__ = "AlldebridCom"
    __type__ = "hoster"
    __version__ = "0.52"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.|s\d+\.)?alldebrid\.com/dl/[\w^_]+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback",
                   "bool",
                   "Fallback to free download if premium fails",
                   False),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int",
                   "Reconnect if waiting time is greater than minutes", 10),
                  ("revert_failed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Alldebrid.com multi-hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Andy Voigt", "spamsales@online.de"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def setup(self):
        self.chunk_limit = 16

    def handle_premium(self, pyfile):
        password = self.get_password()

        html = self.load("http://www.alldebrid.com/service.php",
                         get={'link': pyfile.url,
                              'json': "true",
                              'pseudo': self.account.user,
                              'password': self.account.info['login']['password'],
                              'pw': password})

        json_data = json.loads(html)

        self.log_debug("Json data", json_data)

        if json_data['error']:
            if json_data[
                    'error'] == "This link isn't available on the hoster website.":
                self.offline()

            else:
                self.log_warning(json_data['error'])
                self.temp_offline()

        else:
            if pyfile.name and not pyfile.name.endswith('.tmp'):
                pyfile.name = json_data['filename']

            pyfile.size = parse_size(json_data['filesize'])
            self.link = json_data['link']
