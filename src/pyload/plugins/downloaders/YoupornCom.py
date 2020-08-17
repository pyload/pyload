# -*- coding: utf-8 -*-

import re

from ..base.downloader import BaseDownloader


class YoupornCom(BaseDownloader):
    __name__ = "YoupornCom"
    __type__ = "downloader"
    __version__ = "0.26"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?youporn\.com/watch/.+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Youporn.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("willnix", "willnix@pyload.net")]

    def process(self, pyfile):
        self.pyfile = pyfile

        if not self.file_exists():
            self.offline()

        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())

    def download_html(self):
        url = self.pyfile.url
        self.data = self.load(url, post={"user_choice": "Enter"}, cookies=False)

    def get_file_url(self):
        """
        Returns the absolute downloadable filepath.
        """
        if not self.data:
            self.download_html()

        return re.search(
            r'(http://download\.youporn\.com/download/\d+\?save=1)">', self.data
        ).group(1)

    def get_file_name(self):
        if not self.data:
            self.download_html()

        file_name_pattern = r"<title>(.+) - "
        return (
            re.search(file_name_pattern, self.data)
            .group(1)
            .replace("&amp;", "&")
            .replace("/", "")
            + ".flv"
        )

    def file_exists(self):
        """
        Returns True or False.
        """
        if not self.data:
            self.download_html()
        if re.search(r"(.*invalid video_id.*)", self.data):
            return False
        else:
            return True
