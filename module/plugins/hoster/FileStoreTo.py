# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FileStoreTo(SimpleHoster):
    __name__ = "FileStoreTo"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?filestore\.to/\?d=(?P<ID>\w+)'

    __description__ = """FileStore.to hoster plugin"""
    __author_name__ = ("Walter Purcaro", "stickell")
    __author_mail__ = ("vuolter@gmail.com", "l.stickell@yahoo.it")

    FILE_INFO_PATTERN = r'File: <span[^>]*>(?P<N>.+)</span><br />Size: (?P<S>[\d,.]+) (?P<U>\w+)'
    OFFLINE_PATTERN = r'>Download-Datei wurde nicht gefunden<'


    def setup(self):
        self.resumeDownload = self.multiDL = True

    def handleFree(self):
        self.wait(10)
        ldc = re.search(r'wert="(\w+)"', self.html).group(1)
        link = self.load("http://filestore.to/ajax/download.php", get={"LDC": ldc})
        self.logDebug("Download link = " + link)
        self.download(link)


getInfo = create_getInfo(FileStoreTo)
