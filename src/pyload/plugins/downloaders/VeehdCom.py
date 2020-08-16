# -*- coding: utf-8 -*-
import re

from ..base.downloader import BaseDownloader


class VeehdCom(BaseDownloader):
    __name__ = "VeehdCom"
    __type__ = "downloader"
    __version__ = "0.29"
    __status__ = "testing"

    __pattern__ = r"http://veehd\.com/video/\d+_\S+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("filename_spaces", "bool", "Allow spaces in filename", False),
        ("replacement_char", "str", "Filename replacement character", "_"),
    ]

    __description__ = """Veehd.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("cat", "cat@pyload")]

    def setup(self):
        self.multi_dl = True
        self.req.can_continue = True

    def process(self, pyfile):
        self.download_html()
        if not self.file_exists():
            self.offline()

        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())

    def download_html(self):
        url = self.pyfile.url
        self.log_debug(f"Requesting page: {url}")
        self.data = self.load(url)

    def file_exists(self):
        if not self.data:
            self.download_html()

        if "<title>Veehd</title>" in self.data:
            return False
        return True

    def get_file_name(self):
        if not self.data:
            self.download_html()

        m = re.search(r"<title.*?>(.+?) on Veehd</title>", self.data)
        if m is None:
            self.error(self._("Video title not found"))

        name = m.group(1)

        #: Replace unwanted characters in filename
        if self.config.get("filename_spaces"):
            pattern = r"[^\w ]+"
        else:
            pattern = r"[^\w.]+"

        return re.sub(pattern, self.config.get("replacement_char"), name) + ".avi"

    def get_file_url(self):
        """
        Returns the absolute downloadable filepath.
        """
        if not self.data:
            self.download_html()

        m = re.search(
            r'<embed type="video/divx" src="(http://([^/]*\.)?veehd\.com/dl/.+?)"',
            self.data,
        )
        if m is None:
            self.error(self._("Embedded video url not found"))

        return m.group(1)
