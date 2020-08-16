# -*- coding: utf-8 -*-

#
# Test links:
#   http://d-h.st/mM8


from ..base.simple_downloader import SimpleDownloader


class DevhostSt(SimpleDownloader):
    __name__ = "DevhostSt"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?d-h\.st/(?!users/)\w{3}"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """D-h.st downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]

    NAME_PATTERN = r'<span title="(?P<N>.*?)"'
    SIZE_PATTERN = r"</span> \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)<br"
    HASHSUM_PATTERN = r">(?P<H>.*?) Sum</span>: &nbsp;(?P<D>.*?)<br"

    OFFLINE_PATTERN = r">File Not Found"
    LINK_FREE_PATTERN = r"var product_download_url= \'(.+?)\'"

    def setup(self):
        self.multi_dl = True
        self.chunk_limit = 1
