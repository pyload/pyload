# -*- coding: utf-8 -*-

import re
import urlparse

from ..internal.misc import json
from ..internal.MultiHoster import MultiHoster


class LinksnappyCom(MultiHoster):
    __name__ = "LinksnappyCom"
    __type__ = "hoster"
    __version__ = "0.18"
    __status__ = "testing"

    __pattern__ = r'https?://(?:[^/]+\.)?linksnappy\.com'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", False),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("revert_failed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Linksnappy.com multi-hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it"),
                   ("Bilal Ghouri", None)]

    def handle_premium(self, pyfile):
        host = self._get_host(pyfile.url)
        json_params = json.dumps({'link': pyfile.url,
                                  'type': host,
                                  'username': self.account.user,
                                  'password': self.account.get_login('password')})

        r = self.load("https://linksnappy.com/api/linkgen",
                      post={'genLinks': json_params})

        self.log_debug("JSON data: " + r)

        j = json.loads(r)['links'][0]

        if j['error']:
            self.error(_("Error converting the link"))

        pyfile.name = j['filename']
        self.link = j['generated']

    @staticmethod
    def _get_host(url):
        host = urlparse.urlsplit(url).netloc
        return re.search(r'[\w\-]+\.\w+$', host).group(0)
