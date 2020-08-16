# -*- coding: utf-8 -*-
import re

from ..base.downloader import BaseDownloader


class YesPornPleaseCom(BaseDownloader):
    __name__ = "YesPornPleaseCom"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?yespornplease\.com/view/(\d+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("quality", "240p;360p;480p;720p", "Quality", "720p"),
    ]

    __description__ = """YesPornPlease.Com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("ondrej", "git@ondrej.it")]

    NAME_PATTERN = r"<title>(.+) watch online for free"

    def setup(self):
        self.resume_download = True
        self.multi_dl = True

    def process(self, pyfile):
        resp = self.load(pyfile.url)
        iframe_url = re.findall(r'<iframe src="([^"]+)', resp)
        if not iframe_url:
            self.error(self._("Iframe url not found"))

        iframe_resp = self.load("http:" + iframe_url[0])
        video_url = re.findall(r'<source src="([^"]+)', iframe_resp)
        if not video_url:
            self.error(self._("Video url not found"))

        self.pyfile.name = re.findall(self.NAME_PATTERN, resp)[0]
        self.pyfile.name += "." + video_url[0].split(".")[-1]

        self.log_info(self._("Downloading file..."))

        quality = self.config.get("quality")
        quality_index = ["720p", "480p", "360p", "240p"]
        q = quality_index.index(quality)
        self.download(video_url[q])
