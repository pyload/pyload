# -*- coding: utf-8 -*-

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class TusfilesNet(XFSHoster):
    __name__    = "TusfilesNet"
    __type__    = "hoster"
    __version__ = "0.07"

    __pattern__ = r'https?://(?:www\.)?tusfiles\.net/\w{12}'

    __description__ = """Tusfiles.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"),
                       ("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "tusfiles.net"

    INFO_PATTERN = r'\](?P<N>.+) - (?P<S>[\d.,]+) (?P<U>[\w^_]+)\['
    OFFLINE_PATTERN = r'>File Not Found|<Title>TusFiles - Fast Sharing Files!'


    def setup(self):
        self.multiDL = False
        self.chunkLimit = -1
        self.resumeDownload = True


    def handlePremium(self):
        return self.handleFree()


getInfo = create_getInfo(TusfilesNet)
