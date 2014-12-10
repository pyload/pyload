# -*- coding: utf-8 -*-

import re

from pyload.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FileStoreTo(SimpleHoster):
    __name    = "FileStoreTo"
    __type    = "hoster"
    __version = "0.01"

    __pattern = r'http://(?:www\.)?filestore\.to/\?d=(?P<ID>\w+)'

    __description = """FileStore.to hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]


    INFO_PATTERN = r'File: <span[^>]*>(?P<N>.+)</span><br />Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>Download-Datei wurde nicht gefunden<'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True


    def handleFree(self):
        self.wait(10)
        ldc = re.search(r'wert="(\w+)"', self.html).group(1)
        link = self.load("http://filestore.to/ajax/download.php", get={"LDC": ldc})
        self.download(link)


getInfo = create_getInfo(FileStoreTo)
