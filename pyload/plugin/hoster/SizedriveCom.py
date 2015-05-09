# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class SizedriveCom(SimpleHoster):
    __name    = "SizedriveCom"
    __type    = "hoster"
    __version = "0.01"

    __pattern = r'http://(?:www\.)?sizedrive\.com/[rd]/(?P<ID>\w+)'

    __description = """Sizedrive.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("GammaC0de", None)]


    NAME_PATTERN    = r'>Nome:</b> (?P<N>.+?)<'
    SIZE_PATTERN    = r'>Tamanho:</b>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'ARQUIVO DELATADO POR'


    def setup(self):
        self.resumeDownload = False
        self.multiDL        = False
        self.chunkLimit     = 1


    def handle_free(self, pyfile):
        self.wait(5)
        self.html = self.load("http://www.sizedrive.com/getdownload.php",
                              post={'id': self.info['pattern']['ID']})

        m = re.search(r'<span id="boton_download" ><a href="(.+?)"', self.html)
        if m:
            self.link = m.group(1)
