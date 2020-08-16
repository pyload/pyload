# -*- coding: utf-8 -*-

import re

from pyload.core.network.request_factory import get_url

from ..base.simple_downloader import SimpleDownloader
from ..helpers import format_exc


class OneFichierCom(SimpleDownloader):
    __name__ = "OneFichierCom"
    __type__ = "downloader"
    __version__ = "1.13"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:(?P<ID1>\w+)\.)?(?P<HOST>1fichier\.com|alterupload\.com|cjoint\.net|d(?:es)?fichiers\.com|dl4free\.com|megadl\.fr|mesfichiers\.org|piecejointe\.net|pjointe\.com|tenvoi\.com)(?:/\?(?P<ID2>\w+))?"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """1fichier.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("fragonib", "fragonib[AT]yahoo[DOT]es"),
        ("the-razer", "daniel_ AT gmx DOT net"),
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("imclem", None),
        ("stickell", "l.stickell@yahoo.it"),
        ("Elrick69", "elrick69[AT]rocketmail[DOT]com"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("Ludovic Lehmann", "ludo.lehmann@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    DISPOSITION = False  # TODO: Remove disposition in 0.6.x

    URL_REPLACEMENTS = [
        (
            __pattern__ + ".*",
            lambda m: "https://1fichier.com/?"
            + (m.group("ID1") if m.group("ID1") else m.group("ID2")),
        )
    ]

    COOKIES = [("1fichier.com", "LG", "en")]

    NAME_PATTERN = r">Filename :</td>\s*<td.*>(?P<N>.+?)<"
    SIZE_PATTERN = r">Size :</td>\s*<td.*>(?P<S>[\d.,]+) (?P<U>[\w^_]+)"
    OFFLINE_PATTERN = (
        r"(?:File not found !\s*<)|(?:>The requested file has been deleted)"
    )
    LINK_PATTERN = r'<a href="(.+?)".*>Click here to download the file</a>'
    TEMP_OFFLINE_PATTERN = r"Without subscription, you can only download one file at|Our services are in maintenance"
    PREMIUM_ONLY_PATTERN = r"is not possible to unregistered users|need a subscription"

    WAIT_PATTERN = r">You must wait \d+ minutes"

    def setup(self):
        self.multi_dl = self.premium
        self.chunk_limit = -1 if self.premium else 1
        self.resume_download = True

    @classmethod
    def get_info(cls, url="", html=""):
        redirect = url
        for i in range(10):
            try:
                headers = {
                    k.lower(): v
                    for k, v in re.findall(
                        r"(?P<name>.+?): (?P<value>.+?)\r?\n",
                        get_url(redirect, just_header=True),
                    )
                }
                if "location" in headers and headers["location"]:
                    redirect = headers["location"]

                else:
                    if headers.get("content-type") == "application/octet-stream":
                        if "filename=" in headers.get("content-disposition"):
                            _name = dict(
                                i.strip().split("=")
                                for i in headers["content-disposition"].split(";")[1:]
                            )
                            name = _name["filename"].strip("\"'")
                        else:
                            name = url

                        info = {
                            "name": name,
                            "size": int(headers.get("content-length")),
                            "status": 7,
                            "url": url,
                        }

                    else:
                        info = super(OneFichierCom, cls).get_info(url, html)

                    break

            except Exception as exc:
                print(format_exc())
                info = {"status": 8, "error": exc}
                break

        else:
            info = {"status": 8, "error": "Too many redirects"}

        return info

    def handle_free(self, pyfile):
        url, inputs = self.parse_html_form(r'action="https://1fichier.com/\?[\w^_]+')

        if not url:
            self.log_error(self._("Free download form not found"))
            return

        if "pass" in inputs:
            password = self.get_password()

            if password:
                inputs["pass"] = password

            else:
                self.fail(self._("Download is password protected"))

        inputs.pop("save", None)
        inputs["dl_no_ssl"] = "on"

        self.data = self.load(url, post=inputs)

        self.check_errors()

        m = re.search(self.LINK_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)

    def handle_premium(self, pyfile):
        self.download(
            pyfile.url, post={"did": 0, "dl_no_ssl": "on"}, disposition=False
        )  # TODO: Remove disposition in 0.6.x
