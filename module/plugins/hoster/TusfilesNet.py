# -*- coding: utf-8 -*-

from module.network.HTTPRequest import BadHeader
from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class TusfilesNet(XFSHoster):
    __name__    = "TusfilesNet"
    __type__    = "hoster"
    __version__ = "0.11"

    __pattern__ = r'https?://(?:www\.)?tusfiles\.net/\w{12}'

    __description__ = """Tusfiles.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"),
                       ("guidobelix", "guidobelix@hotmail.it")]


    INFO_PATTERN    = r'\](?P<N>.+) - (?P<S>[\d.,]+) (?P<U>[\w^_]+)\['


    def setup(self):
        self.chunkLimit     = -1
        self.multiDL        = True
        self.resumeDownload = True


    def download(self, url, *args, **kwargs):
        try:
            return super(TusfilesNet, self).download(url, *args, **kwargs)

        except BadHeader, e:
            if e.code is 503:
                self.multiDL = False
                raise Retry("503")


getInfo = create_getInfo(TusfilesNet)
