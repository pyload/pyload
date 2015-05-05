# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class FileStoreTo(SimpleHoster):
    __name    = "FileStoreTo"
    __type    = "hoster"
    __version = "0.05"

    __pattern = r'http://(?:www\.)?filestore\.to/\?d=(?P<ID>\w+)'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """FileStore.to hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]


    INFO_PATTERN         = r'File: <span.*?>(?P<N>.+?)<.*>Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN      = r'>Download-Datei wurde nicht gefunden<'
    TEMP_OFFLINE_PATTERN = r'>Der Download ist nicht bereit !<'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True


    def handle_free(self, pyfile):
        self.wait(10)
        self.link = self.load("http://filestore.to/ajax/download.php",
                              get={'D': re.search(r'"D=(\w+)', self.html).group(1)})
