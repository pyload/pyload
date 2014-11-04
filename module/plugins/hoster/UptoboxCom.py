# -*- coding: utf-8 -*-

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class UptoboxCom(XFSHoster):
    __name__    = "UptoboxCom"
    __type__    = "hoster"
    __version__ = "0.15"

    __pattern__ = r'https?://(?:www\.)?uptobox\.com/\w{12}'

    __description__ = """Uptobox.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    HOSTER_DOMAIN = "uptobox.com"

    INFO_PATTERN = r'"para_title">(?P<N>.+) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)'
    OFFLINE_PATTERN = r'>(File not found|Access Denied|404 Not Found)'

    LINK_PATTERN = r'"(https?://\w+\.uptobox\.com/d/.*?)"'


    def setup(self):
        self.multiDL = True
        self.chunkLimit = 1
        self.resumeDownload = True


getInfo = create_getInfo(UptoboxCom)
