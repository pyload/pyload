# -*- coding: utf-8 -*-

import re
import urllib.parse

from ..base.downloader import BaseDownloader


class XVideosCom(BaseDownloader):
    __name__ = "XVideos.com"
    __type__ = "downloader"
    __version__ = "0.17"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?xvideos\.com/video(\d+)"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """XVideos.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = []

    def process(self, pyfile):
        site = self.load(pyfile.url)
        title_search = re.search(r'<meta\s+property="og:title"\s+content="(.+?)"', site)
        id_search = re.search(self.__pattern__, pyfile.url)
        pyfile.name = "{} ({}).mp4".format(title_search.group(1), id_search.group(1))
        self.download(
            urllib.parse.unquote(
                re.search(r"html5player\.setVideoUrlHigh\(\'(.+?)\'\)", site).group(1)
            )
        )
