# -*- coding: utf-8 -*-

from ..internal.SimpleHoster import SimpleHoster


class GamefrontCom(SimpleHoster):
    __name__ = "GamefrontCom"
    __type__ = "hoster"
    __version__ = "0.13"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?gamefront\.com/files/(?P<ID>\d+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Gamefront.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    NAME_PATTERN = r'<title>(?P<N>.+?) \| Game Front</title>'
    SIZE_PATTERN = r'>File Size:</dt>\s*<dd>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'<p>File not found'

    LINK_FREE_PATTERN = r"downloadUrl = '(.+?)'"

    def setup(self):
        self.resume_download = True
        self.multiDL = True

    def handle_free(self, pyfile):
        self.data = self.load("http://www.gamefront.com/files/service/thankyou",
                              get={'id': self.info['pattern']['ID']})
        return SimpleHoster.handle_free(self, pyfile)
