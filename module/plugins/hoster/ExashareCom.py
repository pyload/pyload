# -*- coding: utf-8 -*-


from ..internal.XFSHoster import XFSHoster


class ExashareCom(XFSHoster):
    __name__ = "ExashareCom"
    __type__ = "hoster"
    __version__ = "0.08"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?exashare\.com/\w{12}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Exashare.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    PLUGIN_DOMAIN = "exashare.com"

    INFO_PATTERN = r'>(?P<NAME>.+?)<small>\( (?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    def setup(self):
        self.multiDL = True
        self.chunk_limit = 1
        self.resume_download = self.premium

    def handle_free(self, pyfile):
        return XFSHoster.handle_free(self, pyfile)
