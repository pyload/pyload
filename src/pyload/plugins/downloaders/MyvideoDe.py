# -*- coding: utf-8 -*-

import re


from ..base.downloader import BaseDownloader
from pyload.core.utils import html_unescape


class MyvideoDe(BaseDownloader):
    __name__ = "MyvideoDe"
    __type__ = "downloader"
    __version__ = "0.96"
    __status__ = "testing"

    __pyload_version__ = "0.5"

    __pattern__ = r"http://(?:www\.)?myvideo\.de/watch/"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Myvideo.de downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("spoob", "spoob@pyload.net")]

    def process(self, pyfile):
        self.pyfile = pyfile
        self.download_html()
        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())

    def download_html(self):
        self.data = self.load(self.pyfile.url)

    def get_file_url(self):
        video_id = re.search(
            r"add_variable\('_videoid','(.*)'\);p.add_param\('quality'", self.data
        ).group(1)
        video_server = re.search(
            "rel='image_src' href='(.*)thumbs/.*' />", self.data
        ).group(1)
        file_url = video_server + video_id + ".flv"
        return file_url

    def get_file_name(self):
        file_name_pattern = r"<h1 class=\'global_hd\'>(.*)</h1>"
        return html_unescape(
            re.search(file_name_pattern, self.data).group(1).replace("/", "") + ".flv"
        )

    def file_exists(self):
        self.download_html()
        self.load(str(self.pyfile.url), cookies=False, just_header=True)
        if self.req.last_effective_url == "http://www.myvideo.de/":
            return False
        return True
