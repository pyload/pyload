# -*- coding: utf-8 -*-
import re

from ..base.downloader import BaseDownloader


class PornovkaCz(BaseDownloader):
    __name__ = "PornovkaCz"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?pornovka\.cz/(.+)"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Pornovka.cz downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("ondrej", "git@ondrej.it")]

    NAME_PATTERN = r"<h1>([^<]+)"

    def setup(self):
        self.resume_download = True
        self.multi_dl = True

    def process(self, pyfile):
        pornovka_resp = self.load(pyfile.url)
        data_url = re.findall(r'data-url="([^"]+)', pornovka_resp)
        if not data_url:
            self.error(self._("Data url not found"))

        data_resp = self.load(data_url[0])
        video_url = re.findall(r"""src=.([^'"]+).></video>""", data_resp)
        if not video_url:
            self.error(self._("Video url not found"))

        # ascii codec can't encode character...
        self.pyfile.name = re.search(self.NAME_PATTERN, pornovka_resp).group(1)
        self.pyfile.name += "." + video_url[0].split(".")[-1]

        self.log_info(self._("Downloading file..."))
        self.download(video_url[0])
