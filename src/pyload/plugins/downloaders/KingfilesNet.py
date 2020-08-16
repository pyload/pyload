# -*- coding: utf-8 -*-
import re

from ..anticaptchas.SolveMedia import SolveMedia
from ..base.simple_downloader import SimpleDownloader


class KingfilesNet(SimpleDownloader):
    __name__ = "KingfilesNet"
    __type__ = "downloader"
    __version__ = "0.13"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?kingfiles\.net/(?P<ID>\w{12})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Kingfiles.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zapp-brannigan", "fuerst.reinje@web.de"),
        ("Walter Purcaro", "vuolter@gmail.com"),
    ]

    NAME_PATTERN = r'name="fname" value="(?P<N>.+?)">'
    SIZE_PATTERN = r'>Size: .+?">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r">(File Not Found</b><br><br>|File Not Found</h2>)"

    RAND_ID_PATTERN = r"type=\"hidden\" name=\"rand\" value=\"(.+)\">"

    LINK_FREE_PATTERN = r"var download_url = \'(.+)\';"

    def setup(self):
        self.resume_download = True
        self.multi_dl = True

    def handle_free(self, pyfile):
        #: Click the free user button
        post_data = {
            "op": "download1",
            "usr_login": "",
            "id": self.info["pattern"]["ID"],
            "fname": pyfile.name,
            "referer": "",
            "method_free": "+",
        }

        self.data = self.load(pyfile.url, post=post_data)

        self.captcha = SolveMedia(pyfile)
        response, challenge = self.captcha.challenge()

        #: Make the downloadlink appear and load the file
        m = re.search(self.RAND_ID_PATTERN, self.data)
        if m is None:
            self.error(self._("Random key not found"))

        rand = m.group(1)
        self.log_debug("rand = " + rand)

        post_data = {
            "op": "download2",
            "id": self.info["pattern"]["ID"],
            "rand": rand,
            "referer": pyfile.url,
            "method_free": "+",
            "method_premium": "",
            "adcopy_response": response,
            "adcopy_challenge": challenge,
            "down_direct": "1",
        }

        self.data = self.load(pyfile.url, post=post_data)

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            self.error(self._("Download url not found"))

        self.link = m.group(1)
