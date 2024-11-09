# -*- coding: utf-8 -*-

from ..base.simple_downloader import SimpleDownloader


class KnigavuheOrg(SimpleDownloader):
    __name__ = "KnigavuheOrg"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"
    __pattern__ = r"https?:\/\/s\d+\.knigavuhe\.org\/.+"

    __authors__ = [("EnergoStalin", "ens.stalin@gmail.com")]
    __license__ = "GPLv3"

    OFFLINE_PATTERN = r">404 Not Found<"

    def setup(self):
        self.multi_dl = True
        self.resume_download = True
        self.chunk_limit = -1
        self.retries = 4

    def handle_direct(self, pyfile):
        [self.link, pyfile.name] = pyfile.url.split("#")
