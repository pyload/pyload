# -*- coding: utf-8 -*-

from ..internal.misc import json, parse_size
from ..internal.MultiHoster import MultiHoster


class AlldebridCom(MultiHoster):
    __name__ = "AlldebridCom"
    __type__ = "hoster"
    __version__ = "0.54"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.|s\d+\.)?alldebrid\.com/dl/[\w^_]+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", False),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("revert_failed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Alldebrid.com multi-hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Andy Voigt", "spamsales@online.de"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://alldebrid.com/apiv2.php"

    def api_response(self, action, **kwargs):
        kwargs['action'] = action
        html = self.load(self.API_URL, get=kwargs)
        return json.loads(html)

    def setup(self):
        self.chunk_limit = 16

    def handle_premium(self, pyfile):
        json_data = self.api_response("unlock", link=pyfile.url, uid=self.account.info['data']['cookie'])

        if json_data['error']:
            if json_data['error'] == "This link is not available on the file hoster website":
                self.offline()

            else:
                self.log_warning(json_data['error'])
                self.temp_offline()

        else:
            pyfile.name = json_data['filename']
            pyfile.size = parse_size(json_data['filesize'])
            self.link = json_data['link']
