# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class SizedriveCom(SimpleHoster):
    __name__    = "SizedriveCom"
    __type__    = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?sizedrive\.com/[rd]/(?P<ID>\w+)'

    __description__ = """Sizedrive.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("GammaC0de", None)]


    OFFLINE_PATTERN = r'ARQUIVO DELATADO POR'
    NAME_PATTERN = r'<b>Nome:</b> (?P<N>.+)<'
    SIZE_PATTERN = r'<b>Tamanho:</b>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    def setup(self):
        self.resumeDownload = False
        self.multiDL        = False
        self.chunkLimit     = 1


    def handleFree(self, pyfile):
        self.wait(5)
        self.html = self.load("http://www.sizedrive.com/getdownload.php",
                              post={'id': self.info['pattern']['ID']})

        m = re.search(r'<span id="boton_download" ><a href="(.+?)"', self.html)
        if m:
            self.link = m.group(1)
        else:
            self.error(_("Download link not found"))


getInfo = create_getInfo(SizedriveCom)
