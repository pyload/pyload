# -*- coding: utf-8 -*-

import re

from ..base.simple_downloader import SimpleDownloader


class PorntrexCom(SimpleDownloader):
    __name__ = "PorntrexCom"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?porntrex\.com/video/.+"

    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("quality", "360p;480p;720p;1080p;1440p;2160p", "Quality Setting", "1080p"),
    ]

    __description__ = """Porntrex.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("ondrej", "git@ondrej.it")]

    NAME_PATTERN = r'<p class="title-video">(?P<N>.+?)</p>'
    OFFLINE_PATTERN = r"<title>page not found</title>"

    DISPOSITION = False

    def setup(self):
        self.multi_dl = True
        self.resume_download = False

    def handle_free(self, pyfile):
        html = self.load(pyfile.url)

        quality = self.config.get("quality")
        all_quality = ["2160p", "1440p", "1080p", "720p", "480p", "360p"]

        for i in all_quality[all_quality.index(quality) :]:
            video_url = re.findall(
                r"https://www.porntrex.com/get_file/[\w\d/]+_{0}.mp4".format(i), html
            )
            if video_url:
                self.link = video_url[0]
                break

        if not self.link:
            self.error(self._("Video URL not found"))

        self.pyfile.name = re.search(self.NAME_PATTERN, html).group(1)
        self.pyfile.name += "." + self.link.split(".")[-1]
