# -*- coding: utf-8 -*-

import re

from ..internal.Hoster import Hoster
from ..internal.misc import html_unescape


class MyvideoDe(Hoster):
    __name__ = "MyvideoDe"
    __type__ = "hoster"
    __version__ = "0.96"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?myvideo\.de/watch/'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Myvideo.de hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("spoob", "spoob@pyload.org")]

    def process(self, pyfile):
        self.pyfile = pyfile
        self.download_html()
        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())

    def download_html(self):
        self.data = self.load(self.pyfile.url)

    def get_file_url(self):
        videoId = re.search(
            r"addVariable\('_videoid','(.*)'\);p.addParam\('quality'", self.data).group(1)
        videoServer = re.search(
            "rel='image_src' href='(.*)thumbs/.*' />",
            self.data).group(1)
        file_url = videoServer + videoId + ".flv"
        return file_url

    def get_file_name(self):
        file_name_pattern = r'<h1 class=\'globalHd\'>(.*)</h1>'
        return html_unescape(re.search(file_name_pattern, self.data).group(
            1).replace("/", "") + '.flv')

    def file_exists(self):
        self.download_html()
        self.load(str(self.pyfile.url), cookies=False, just_header=True)
        if self.req.lastEffectiveURL == "http://www.myvideo.de/":
            return False
        return True
