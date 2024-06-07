# -*- coding: utf-8 -*-

from ..base.simple_downloader import SimpleDownloader


class SKnigavuhe(SimpleDownloader):
    __name__ = "SKnigavuhe"
    __type__ = "downloader"
    __version__ = "0.1"
    __status__ = "testing"
    __pattern__ = (
        r"https?:\/\/s\d+\.knigavuhe\.org\/\d+\/audio\/\d+\/[0-9a-z\-]+\.mp3.+"
    )

    __authors__ = [("EnergoStalin", "ens.stalin@gmail.com")]
    __license__ = "GPLv3"

    OFFLINE_PATTERN = r">404 Not Found<"

    def handle_direct(self, pyfile):
        [self.link, pyfile.name] = pyfile.url.split("#")
