# -*- coding: utf-8 -*-

#
# Test links:
# http://speedy.sh/ep2qY/Zapp-Brannigan.jpg

import re

from ..base.simple_downloader import SimpleDownloader


class SpeedyshareCom(SimpleDownloader):
    __name__ = "SpeedyshareCom"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(speedyshare\.com|speedy\.sh)/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Speedyshare.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]

    NAME_PATTERN = r"class=downloadfilename>(?P<N>.*)</span></td>"
    SIZE_PATTERN = r"class=sizetagtext>(?P<S>.*) (?P<U>[kKmM]?[iI]?[bB]?)</div>"

    OFFLINE_PATTERN = r"class=downloadfilenamenotfound>.*</span>"

    LINK_FREE_PATTERN = r"<a href=\'(.*)\'><img src=/gf/slowdownload\.png alt=\'Slow Download\' border=0"

    def setup(self):
        self.multi_dl = False
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            self.link = m.group(1)
