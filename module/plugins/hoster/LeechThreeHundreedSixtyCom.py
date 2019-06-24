# -*- coding: utf-8 -*-

from ..internal.MultiHoster import MultiHoster
from ..internal.misc import json, parse_size

class LeechThreeHundreedSixtyCom(MultiHoster):
    __name__ = "LeechThreeHundreedSixtyCom"
    __type__ = "hoster"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", False),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("revert_failed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Leech360.com multi-hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def handle_premium(self, pyfile):
        json_data = self.load("https://leech360.com/generate",
                              get={'token': self.account.info['data']['token'],
                                   'link': pyfile.url})
        api_data = json.loads(json_data)

        if api_data['error']:
            self.fail(api_data['error_message'])

        pyfile.name = api_data.get('filename', "") or pyfile.name
        pyfile.size = parse_size(api_data.get('message', "0"))
        self.link = api_data['download_url']



