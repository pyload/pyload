# -*- coding: utf-8 -*-

#
# Test links:
# https://goo.im/devs/liquidsmooth/3.x/codina/Nightly/LS-KK-v3.2-2014-08-01-codina.zip


from ..base.simple_downloader import SimpleDownloader


class GooIm(SimpleDownloader):
    __name__ = "GooIm"
    __type__ = "downloader"
    __version__ = "0.09"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?goo\.im/.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Goo.im downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]

    NAME_PATTERN = r"You will be redirected to .*(?P<N>[^/ ]+)  in"
    OFFLINE_PATTERN = r"The file you requested was not found"

    def setup(self):
        self.resume_download = True
        self.multi_dl = True

    def handle_free(self, pyfile):
        self.wait(10)
        self.link = pyfile.url
