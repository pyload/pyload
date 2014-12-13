# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster, create_getInfo


class TusfilesNet(XFSHoster):
    __name    = "TusfilesNet"
    __type    = "hoster"
    __version = "0.07"

    __pattern = r'https?://(?:www\.)?tusfiles\.net/\w{12}'

    __description = """Tusfiles.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com"),
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
