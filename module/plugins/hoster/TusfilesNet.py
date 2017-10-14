# -*- coding: utf-8 -*-

from module.network.HTTPRequest import BadHeader

from ..internal.Plugin import Retry
from ..internal.XFSHoster import XFSHoster


class TusfilesNet(XFSHoster):
    __name__ = "TusfilesNet"
    __type__ = "hoster"
    __version__ = "0.18"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?tusfiles\.net/\w{12}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Tusfiles.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("guidobelix", "guidobelix@hotmail.it")]

    PLUGIN_DOMAIN = "tusfiles.net"

    INFO_PATTERN = r'\](?P<N>.+) - (?P<S>[\d.,]+) (?P<U>[\w^_]+)\['

    def setup(self):
        self.chunk_limit = -1
        self.multiDL = True
        self.limitDL = 2
        self.resume_download = True

    def download(self, url, *args, **kwargs):
        try:
            return XFSHoster.download(self, url, *args, **kwargs)

        except BadHeader, e:
            if e.code == 503:
                self.multiDL = False
                raise Retry("503")
