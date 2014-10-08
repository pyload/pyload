# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class TusfilesNet(XFSPHoster):
    __name__ = "TusfilesNet"
    __type__ = "hoster"
    __version__ = "0.06"

    __pattern__ = r'https?://(?:www\.)?tusfiles\.net/\w{12}'

    __description__ = """Tusfiles.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_NAME = "tusfiles.net"

    FILE_INFO_PATTERN = r'\](?P<N>.+) - (?P<S>[\d.]+) (?P<U>\w+)\['
    OFFLINE_PATTERN = r'>File Not Found|<Title>TusFiles - Fast Sharing Files!'


    def setup(self):
        self.multiDL = False
        self.chunkLimit = -1
        self.resumeDownload = True


    def handlePremium(self):
        return self.handleFree()


getInfo = create_getInfo(TusfilesNet)
