# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FileStoreTo(SimpleHoster):
    __name__    = "FileStoreTo"
    __type__    = "hoster"
    __version__ = "0.05"

    __pattern__ = r'http://(?:www\.)?filestore\.to/\?d=(?P<ID>\w+)'

    __description__ = """FileStore.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]


    INFO_PATTERN         = r'File: <span.*?>(?P<N>.+?)<.*>Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN      = r'>Download-Datei wurde nicht gefunden<'
    TEMP_OFFLINE_PATTERN = r'>Der Download ist nicht bereit !<'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True


    def handleFree(self, pyfile):
        self.wait(10)
        self.link = self.load("http://filestore.to/ajax/download.php",
                              get={'D': re.search(r'"D=(\w+)', self.html).group(1)})


getInfo = create_getInfo(FileStoreTo)
