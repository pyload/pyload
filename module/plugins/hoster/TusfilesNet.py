# -*- coding: utf-8 -*-

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class TusfilesNet(XFileSharingPro):
    __name__ = "TusfilesNet"
    __type__ = "hoster"
    __version__ = "0.04"

    __pattern__ = r'https?://(?:www\.)?tusfiles\.net/(?P<ID>\w+)'

    __description__ = """Tusfiles.net hoster plugin"""
    __author_name__ = ("Walter Purcaro", "guidobelix")
    __author_mail__ = ("vuolter@gmail.com", "guidobelix@hotmail.it")

    HOSTER_NAME = "tusfiles.net"

    FILE_INFO_PATTERN = r'\](?P<N>.+) - (?P<S>[\d.]+) (?P<U>\w+)\['
    OFFLINE_PATTERN = r'>File Not Found|<Title>TusFiles - Fast Sharing Files!'

    SH_COOKIES = [(".tusfiles.net", "lang", "english")]


    def setup(self):
        self.multiDL = False
        self.chunkLimit = -1
        self.resumeDownload = True

    def handlePremium(self):
        url = self.getDownloadLink()
        self.logDebug("Download URL: %s" % url)
        self.startDownload(url)



getInfo = create_getInfo(TusfilesNet)
