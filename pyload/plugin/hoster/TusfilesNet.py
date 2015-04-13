# -*- coding: utf-8 -*-

from pyload.network.HTTPRequest import BadHeader
from pyload.plugin.internal.XFSHoster import XFSHoster


class TusfilesNet(XFSHoster):
    __name    = "TusfilesNet"
    __type    = "hoster"
    __version = "0.10"

    __pattern = r'https?://(?:www\.)?tusfiles\.net/\w{12}'

    __description = """Tusfiles.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com"),
                       ("guidobelix", "guidobelix@hotmail.it")]


    INFO_PATTERN    = r'\](?P<N>.+) - (?P<S>[\d.,]+) (?P<U>[\w^_]+)\['
    OFFLINE_PATTERN = r'>File Not Found|<Title>TusFiles - Fast Sharing Files!|The file you are trying to download is no longer available'


    def setup(self):
        self.chunkLimit     = -1
        self.multiDL        = True
        self.resumeDownload = True


    def downloadLink(self, link, disposition=True):
        try:
            return super(TusfilesNet, self).downloadLink(link, disposition)

        except BadHeader, e:
            if e.code is 503:
                self.multiDL = False
                raise Retry("503")
