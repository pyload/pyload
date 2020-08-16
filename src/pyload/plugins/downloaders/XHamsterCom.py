# -*- coding: utf-8 -*-
import json
import re

from ..base.downloader import BaseDownloader


def quality_fallback(desired, available):
    result = available.get(desired, None)
    if result is None:
        if desired == "720p":
            return quality_fallback("480p", available)
        elif desired == "480p":
            return quality_fallback("240p", available)
        else:
            # Return the entry starting with the lowest digit (shoud be 240p)
            (quality, result) = sorted(
                available.items(), key=lambda x: x[0], reverse=True
            )[0]

    return result


class XHamsterCom(BaseDownloader):
    __name__ = "XHamsterCom"
    __type__ = "downloader"
    __version__ = "0.19"
    __status__ = "testing"

    __pattern__ = r"https?://(?:\w+\.)?xhamster\.com/videos/.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("quality", "720p;480p;240p", "Preferred quality", "480p"),
    ]

    __description__ = """XHamster.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = []

    def process(self, pyfile):
        self.pyfile = pyfile

        if not self.file_exists():
            self.offline()

        quality = self.config.get("quality")
        self.desired_quality = quality if quality is not None else "480p"

        pyfile.name = self.get_file_name() + "." + self.desired_quality + ".mp4"
        self.download(self.get_file_url())

    def download_html(self):
        url = self.pyfile.url
        self.data = self.load(url)

    def get_file_url(self):
        """
        Returns the absolute downloadable filepath.
        """
        if not self.data:
            self.download_html()

        video_data_re = r'(?ms)<script\s+id="initials-script"\s*>.*?window\.initials\s*=\s*({.*?});\s*<\/script>'
        video_data_search = re.search(video_data_re, self.data)

        if not video_data_search:
            self.error(self._("video data not found"))

        video_data = json.loads(video_data_search.group(1))

        video_model = video_data.get("videoModel", None)
        if video_model is None:
            self.error(self._("Could not find video model!"))

        sources = video_model.get("sources", None)
        if sources is None:
            self.error(self._("Could not find sources!"))

        mp4_sources = sources.get("mp4", None)
        if mp4_sources is None:
            self.error(self._("Could not find mp4 sources!"))

        long_url = quality_fallback(self.desired_quality, mp4_sources)

        return long_url

    def get_file_name(self):
        if not self.data:
            self.download_html()

        pattern = r'<meta.*?property="og:title"\s+content="(.+?)"'
        name = re.search(pattern, self.data)
        return name.group(1) if name is not None else "Unknown"

    def file_exists(self):
        """
        Returns True or False.
        """
        if not self.data:
            self.download_html()
        if re.search(r"(.*Video not found.*)", self.data):
            return False
        else:
            return True
