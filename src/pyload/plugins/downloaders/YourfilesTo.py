# -*- coding: utf-8 -*-
import re
import urllib.parse

from ..base.downloader import BaseDownloader


class YourfilesTo(BaseDownloader):
    __name__ = "YourfilesTo"
    __type__ = "downloader"
    __version__ = "0.28"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?yourfiles\.(to|biz)/\?d=\w+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Youfiles.to downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("jeix", "jeix@hasnomail.de"),
        ("skydancer", "skydancer@hasnomail.de"),
    ]

    def process(self, pyfile):
        self.pyfile = pyfile
        self.prepare()
        self.download(self.get_file_url())

    def prepare(self):
        if not self.file_exists():
            self.offline()

        self.pyfile.name = self.get_file_name()

        self.wait(self.get_waiting_time())

    def get_waiting_time(self):
        if not self.data:
            self.download_html()

        #: var zzipitime = 15
        m = re.search(r"var zzipitime = (\d+);", self.data)
        if m is not None:
            sec = int(m.group(1))
        else:
            sec = 0

        return sec

    def download_html(self):
        url = self.pyfile.url
        self.data = self.load(url)

    def get_file_url(self):
        """
        Returns the absolute downloadable filepath.
        """
        url = re.search(r"var bla = '(.*?)';", self.data)
        if url:
            url = url.group(1)
            url = urllib.parse.unquote(
                url.replace("http://http:/http://", "http://").replace("dumdidum", "")
            )
            return url
        else:
            self.error(self._("Absolute filepath not found"))

    def get_file_name(self):
        if not self.data:
            self.download_html()

        return re.search("<title>(.*)</title>", self.data).group(1)

    def file_exists(self):
        """
        Returns True or False.
        """
        if not self.data:
            self.download_html()

        if re.search(r"HTTP Status 404", self.data):
            return False
        else:
            return True
