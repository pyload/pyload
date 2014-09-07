# -*- coding: utf-8 -*-

from pyload.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class TusfilesNet(XFileSharingPro):
    __name__ = "TusfilesNet"
    __type__ = "hoster"
    __version__ = "0.03"

    __pattern__ = r'https?://(?:www\.)?tusfiles\.net/(?P<ID>\w+)'

    __description__ = """Tusfiles.net hoster plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    HOSTER_NAME = "tusfiles.net"

    FILE_INFO_PATTERN = r'\](?P<N>.+) - (?P<S>[\d.]+) (?P<U>\w+)\['
    OFFLINE_PATTERN = r'>File Not Found|<Title>TusFiles - Fast Sharing Files!'

    SH_COOKIES = [(".tusfiles.net", "lang", "english")]


    def setup(self):
        self.multiDL = False
        self.chunkLimit = -1
        self.resumeDownload = True


getInfo = create_getInfo(TusfilesNet)
