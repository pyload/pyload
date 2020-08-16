# -*- coding: utf-8 -*-
import re
import urllib.parse

import pycurl
from pyload.core.utils import parse

from ..base.downloader import BaseDownloader


class Ftp(BaseDownloader):
    __name__ = "Ftp"
    __type__ = "downloader"
    __version__ = "0.61"
    __status__ = "testing"

    __pattern__ = r"(?:ftps?|sftp)://([\w\-.]+(:[\w\-.]+)?@)?[\w\-.]+(:\d+)?/.+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Download from ftp directory"""
    __license__ = "GPLv3"
    __authors__ = [
        ("jeix", "jeix@hasnomail.com"),
        ("mkaay", "mkaay@mkaay.de"),
        ("zoidberg", "zoidberg@mujmail.cz"),
    ]

    def setup(self):
        self.chunk_limit = -1
        self.resume_download = True

    def process(self, pyfile):
        p_url = urllib.parse.urlparse(pyfile.url)
        netloc = p_url.netloc

        pyfile.name = parse.name(p_url.path.rpartition("/")[2])

        if "@" not in netloc:
            # TODO: Recheck in 0.6.x
            if self.account:
                servers = [x["login"] for x in self.account.get_all_accounts()]
            else:
                servers = []

            if netloc in servers:
                self.log_debug(f"Logging on to {netloc}")
                self.req.add_auth(self.account.get_login("password"))

            else:
                pwd = self.get_password()
                if ":" in pwd:
                    self.log_debug(f"Logging on to {netloc}")
                    self.req.add_auth(pwd)
                else:
                    self.log_debug("Using anonymous logon")

        try:
            headers = self.load(pyfile.url, just_header=True)

        except pycurl.error as exc:
            if "530" in exc.args[1]:
                self.fail(self._("Authorization required"))
            else:
                self.fail(self._("Error {}: {}").format(exc.args))

        self.req.http.c.setopt(pycurl.NOBODY, 0)
        self.log_debug(self.req.http.header)

        if "content-length" in headers:
            pyfile.size = headers.get("content-length")
            self.download(pyfile.url)

        else:
            #: Naive ftp directory listing
            if re.search(r'^25\d.*?"', self.req.http.header, re.M):
                pyfile.url = pyfile.url.rstrip("/")
                pkgname = "/".join(
                    [
                        pyfile.package().name,
                        urllib.parse.urlparse(pyfile.url).path.rpartition("/")[2],
                    ]
                )

                pyfile.url += "/"

                self.req.http.c.setopt(48, 1)  #: CURLOPT_DIRLISTONLY
                res = self.load(pyfile.url, decode=False)

                links = [pyfile.url + x for x in res.splitlines()]
                self.log_debug("LINKS", links)

                self.pyload.api.addPackage(pkgname, links)

            else:
                self.fail(self._("Unexpected server response"))
