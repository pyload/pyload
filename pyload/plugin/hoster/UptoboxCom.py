# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster


class UptoboxCom(XFSHoster):
    __name    = "UptoboxCom"
    __type    = "hoster"
    __version = "0.18"

    __pattern = r'https?://(?:www\.)?(uptobox|uptostream)\.com/\w{12}'

    __description = """Uptobox.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    INFO_PATTERN         = r'"para_title">(?P<N>.+) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)'
    OFFLINE_PATTERN      = r'>(File not found|Access Denied|404 Not Found)'
    TEMP_OFFLINE_PATTERN = r'>Service Unavailable'

    LINK_PATTERN = r'"(https?://\w+\.uptobox\.com/d/.*?)"'

    ERROR_PATTERN = r'>(You have to wait.+till next download.)<'  #@TODO: Check XFSHoster ERROR_PATTERN


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1
        self.resumeDownload = True
