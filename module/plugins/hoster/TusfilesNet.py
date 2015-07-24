# -*- coding: utf-8 -*-

from module.network.HTTPRequest import BadHeader
from module.plugins.internal.Plugin import Retry
from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class TusfilesNet(XFSHoster):
    __name__    = "TusfilesNet"
    __type__    = "hoster"
    __version__ = "0.12"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?tusfiles\.net/\w{12}'

    __description__ = """Tusfiles.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"),
                       ("guidobelix", "guidobelix@hotmail.it")]


    INFO_PATTERN    = r'\](?P<N>.+) - (?P<S>[\d.,]+) (?P<U>[\w^_]+)\['


    def setup(self):
        self.chunk_limit     = -1
        self.multiDL        = True
        self.resume_download = True


    def download(self, url, *args, **kwargs):
        try:
            return super(TusfilesNet, self).download(url, *args, **kwargs)

        except BadHeader, e:
            if e.code == 503:
                self.multiDL = False
                raise Retry("503")


getInfo = create_getInfo(TusfilesNet)
