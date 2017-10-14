# -*- coding: utf-8 -*-

import re

from ..internal.SimpleHoster import SimpleHoster


class SizedriveCom(SimpleHoster):
    __name__ = "SizedriveCom"
    __type__ = "hoster"
    __version__ = "0.07"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?sizedrive\.com/[rd]/(?P<ID>\w+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Sizedrive.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", None)]

    NAME_PATTERN = r'>Nome:</b> (?P<N>.+?)<'
    SIZE_PATTERN = r'>Tamanho:</b>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'ARQUIVO DELATADO POR'

    def setup(self):
        self.resume_download = False
        self.multiDL = False
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        self.wait(5)
        self.data = self.load("http://www.sizedrive.com/getdownload.php",
                              post={'id': self.info['pattern']['ID']})

        m = re.search(r'<span id="boton_download" ><a href="(.+?)"', self.data)
        if m is not None:
            self.link = m.group(1)
