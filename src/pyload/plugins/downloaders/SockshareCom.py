# -*- coding: utf-8 -*-

from ..base.dead_downloader import DeadDownloader


class SockshareCom(DeadDownloader):
    __name__ = "SockshareCom"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?sockshare\.com/(mobile/)?(file|embed)/(?P<ID>\w+)"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Sockshare.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("jeix", "jeix@hasnomail.de"),
        ("stickell", "l.stickell@yahoo.it"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]
