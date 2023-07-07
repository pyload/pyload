# -*- coding: utf-8 -*

#
# Test links:
#   https://drive.google.com/file/d/0B6RNTe4ygItBQm15RnJiTmMyckU/view?pli=1


import json
import re
import urllib.parse

from pyload.core.network.http.exceptions import BadHeader
from pyload.core.utils import parse

from ..base.downloader import BaseDownloader


class GoogledriveCom(BaseDownloader):
    __name__ = "GoogledriveCom"
    __type__ = "downloader"
    __version__ = "0.35"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:drive|docs)\.google\.com/(?:file/d/|uc\?.*id=)(?P<ID>[-\w]+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Drive.google.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zapp-brannigan", "fuerst.reinje@web.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    INFO_PATTERN = r'<span class="uc-name-size"><a href="[^"]+">(?P<N>.+?)</a> \((?P<S>[\d.,]+)(?P<U>[\w^_]+)\)</span>'

    API_URL = "https://www.googleapis.com/drive/v3/"
    API_KEY = "AIzaSyB68u-qFPP9oBJpo1DWAPFE_VD2Sfy9hpk"

    def setup(self):
        self.multi_dl = True
        self.resume_download = True
        self.chunk_limit = 1

    def api_request(self, cmd, **kwargs):
        kwargs["key"] = self.API_KEY
        try:
            json_data = json.loads(
                self.load("{}{}".format(self.API_URL, cmd), get=kwargs)
            )
            self.log_debug(f"API response: {json_data}")
            return json_data

        except BadHeader as exc:
            try:
                json_data = json.loads(exc.content)
                self.log_error(
                    "API Error: {}".format(cmd),
                    json_data["error"]["message"],
                    "ID: {}".format(self.info["pattern"]["ID"]),
                    "Error code: {}".format(exc.code),
                )

            except ValueError:
                self.log_error(
                    "API Error: {}".format(cmd),
                    exc,
                    "ID: {}".format(self.info["pattern"]["ID"]),
                    "Error code: {}".format(exc.code),
                )
            return None

    def api_download(self, disposition):
        try:
            self.download(
                "{}{}/{}".format(self.API_URL, "files", self.info["pattern"]["ID"]),
                get={
                    "alt": "media",
                    "acknowledgeAbuse": "true",
                    "supportsAllDrives": "true",
                    "key": self.API_KEY,
                },
                disposition=disposition
            )

        except BadHeader as exc:
            if exc.code == 404:
                self.offline()

            elif exc.code == 403:
                self.temp_offline()

            else:
                raise

    def process(self, pyfile):
        disposition = False
        json_data = self.api_request(
            "files/" + self.info["pattern"]["ID"],
            fields="md5Checksum,name,size",
            supportsAllDrives="true",
        )

        if json_data is None:
            self.fail("API error")

        self.data = self.load(pyfile.url, ref=False)
        if "error" in json_data:
            if json_data["error"]["code"] == 404:
                if "Virus scan warning" not in self.data:
                    self.offline()

                else:
                    m = re.search(self.INFO_PATTERN, self.data)
                    if m is not None:
                        pyfile.name = m.group("N")
                        pyfile.size = parse.bytesize(m.group("S"), m.group("U"))
                    else:
                        disposition = True

            else:
                self.fail(json_data["error"]["message"])

        else:
            pyfile.size = int(json_data["size"])
            pyfile.name = json_data["name"]
            self.info["md5"] = json_data["md5Checksum"]

        # Somehow, API downloads are significantly slow compared to "normal" download :(
        # self.api_download(disposition)

        for _i in range(2):
            m = re.search(r'"([^"]+uc\?.*?)"', self.data)
            if m is None:
                if "Quota exceeded" in self.data:
                    self.temp_offline()
                else:
                    self.fail(self._("link pattern not found"))

            link = re.sub(
                r"\\[uU]([\da-fA-F]{4})", lambda x: chr(int(x.group(1), 16)), m.group(1)
            )  #: unescape unicode-escape
            link = urllib.parse.urljoin(pyfile.url, link)

            #: "Only files smaller than 100 MB can be scanned for viruses"
            #: https://support.google.com/a/answer/172541?hl=en
            if pyfile.size > 104857600 or "Virus scan warning" in self.data:
                if re.search(r"/uc\?.*&confirm=", link):
                    self.download(link, disposition=disposition)
                    break

                else:
                    self.data = self.load(link)

            else:
                self.download(link, disposition=disposition)
                break
