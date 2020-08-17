# -*- coding: utf-8 -*-

import re

from ..base.downloader import BaseDownloader


class PornhostCom(BaseDownloader):
    __name__ = "PornhostCom"
    __type__ = "downloader"
    __version__ = "0.26"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?pornhost\.com/(\d+/\d+\.html|\d+)"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Pornhost.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("jeix", "jeix@hasnomail.de")]

    def process(self, pyfile):
        self.download_html()
        if not self.file_exists():
            self.offline()

        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())

    #: Old interface
    def download_html(self):
        url = self.pyfile.url
        self.data = self.load(url)

    def get_file_url(self):
        """
        Returns the absolute downloadable filepath.
        """
        if not self.data:
            self.download_html()

        url = re.search(r'download this file</label>.*?<a href="(.*?)"', self.data)
        if url is None:
            url = re.search(
                r'"(http://dl\d+\.pornhost\.com/files/.*?/.*?/.*?/.*?/.*?/.*?\..*?)"',
                self.data,
            )
            if url is None:
                url = re.search(
                    r'width: 894px; height: 675px">.*?<img src="(.*?)"', self.data
                )
                if url is None:
                    url = re.search(
                        r'"http://file\d+\.pornhost\.com/\d+/.*?"', self.data
                    )  # TODO: fix this one since it doesn't match

        return url.group(1)

    def get_file_name(self):
        if not self.data:
            self.download_html()

        name = re.search(
            r"<title>pornhost\.com - free file hosting with a twist - gallery(.*?)</title>",
            self.data,
        )
        if name is None:
            name = re.search(
                r'id="url" value="http://www\.pornhost\.com/(.*?)/"', self.data
            )
            if name is None:
                name = re.search(
                    r"<title>pornhost\.com - free file hosting with a twist -(.*?)</title>",
                    self.data,
                )
                if name is None:
                    name = re.search(
                        r'"http://file\d+\.pornhost\.com/.*?/(.*?)"', self.data
                    )

        name = name.group(1).strip() + ".flv"

        return name

    def file_exists(self):
        """
        Returns True or False.
        """
        if not self.data:
            self.download_html()

        if re.search(r"gallery not found|You will be redirected to", self.data):
            return False
        else:
            return True
