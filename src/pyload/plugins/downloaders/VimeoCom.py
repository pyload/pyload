# -*- coding: utf-8 -*-
import json
import re
import urllib.parse

from ..base.simple_downloader import SimpleDownloader


class VimeoCom(SimpleDownloader):
    __name__ = "VimeoCom"
    __type__ = "downloader"
    __version__ = "0.12"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(player\.)?vimeo\.com/(video/)?(?P<ID>\d+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("quality", "Lowest;360p;540p;720p;1080p;Highest", "Quality", "Highest"),
    ]

    __description__ = """Vimeo.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    NAME_PATTERN = r"<title>(?P<N>.+?) on Vimeo<"
    OFFLINE_PATTERN = r'class="exception_header"'
    TEMP_OFFLINE_PATTERN = r"Please try again in a few minutes.<"

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"https://vimeo.com/\g<ID>")]

    COOKIES = [("vimeo.com", "language", "en")]

    @classmethod
    def get_info(cls, url="", html=""):
        info = super(VimeoCom, cls).get_info(url, html)
        # Unfortunately, NAME_PATTERN does not include file extension so we blindly add '.mp4' as an extension.
        # (hopefully all links are '.mp4' files)
        if "name" in info:
            info["name"] += ".mp4"

        return info

    def setup(self):
        self.resume_download = True
        self.multi_dl = True
        self.chunk_limit = -1

    def handle_free(self, pyfile):
        url, inputs = self.parse_html_form('id="pw_form"')
        if url:
            password = self.get_password()

            if not password:
                self.fail(self._("Video is password protected"))

            token = re.search(r'"vimeo":{"xsrft":"(.+?)"}', self.data).group(1)
            inputs["token"] = token
            inputs["password"] = password

            self.data = self.load(urllib.parse.urljoin(pyfile.url, url), post=inputs)

            if "Sorry, that password was incorrect. Please try again." in self.data:
                self.fail(self._("Wrong password"))

        m = re.search(r"clip_page_config = ({.+?});", self.data)
        if m is None:
            self.fail("Clip config pattern not found")

        player_config_url = json.loads(m.group(1))["player"]["config_url"]

        json_data = self.load(player_config_url)

        if not json_data.startswith("{"):
            self.fail(self._("Unexpected response, expected JSON data"))

        json_data = json.loads(json_data)

        videos = {
            v["quality"]: v["url"] for v in json_data["request"]["files"]["progressive"]
        }

        quality = self.config.get("quality")
        if quality == "Highest":
            qlevel = ("1080p", "720p", "540p", "360p")

        elif quality == "Lowest":
            qlevel = ("360p", "540p", "720p", "1080p")

        else:
            qlevel = quality

        for q in qlevel:
            if q in videos.keys():
                self.download(videos[q], fixurl=False)
                return

            else:
                self.log_info(self._("No {} quality video found").format(q))
        else:
            self.fail(self._("No video found!"))
