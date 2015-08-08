# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class SizedriveCom(SimpleHoster):
    __name__    = "SizedriveCom"
    __type__    = "hoster"
    __version__ = "0.03"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?sizedrive\.com/[rd]/(?P<ID>\w+)'

    __description__ = """Sizedrive.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("GammaC0de", None)]


    NAME_PATTERN    = r'>Nome:</b> (?P<N>.+?)<'
    SIZE_PATTERN    = r'>Tamanho:</b>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'ARQUIVO DELATADO POR'


    def setup(self):
        self.resume_download = False
        self.multiDL        = False
        self.chunk_limit     = 1


    def handle_free(self, pyfile):
        self.wait(5)
        self.html = self.load("http://www.sizedrive.com/getdownload.php",
                              post={'id': self.info['pattern']['ID']})

        m = re.search(r'<span id="boton_download" ><a href="(.+?)"', self.html)
        if m:
            self.link = m.group(1)


getInfo = create_getInfo(SizedriveCom)
