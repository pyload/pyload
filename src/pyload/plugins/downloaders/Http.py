# -*- coding: utf-8 -*-

import re
import urllib.parse

from pyload.core.network.http.exceptions import BadHeader

from ..base.downloader import BaseDownloader


class Http(BaseDownloader):
    __name__ = "Http"
    __type__ = "downloader"
    __version__ = "0.10"
    __status__ = "testing"

    __pattern__ = r"(?:jd|pys?)://.+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Download simple http link"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def setup(self):
        self.chunk_limit = -1
        self.resume_download = True

    def process(self, pyfile):
        url = re.sub(r"^(jd|py)", "http", pyfile.url)
        netloc = urllib.parse.urlparse(url).netloc

        for _ in range(2):
            try:
                self.download(url, ref=False, disposition=True)

            except BadHeader as exc:
                if exc.code not in (401, 403, 404, 410):
                    raise

            if self.req.code in (404, 410):
                self.offline()

            elif self.req.code in (401, 403):
                self.log_debug(
                    "Auth required", f"Received HTTP status code: {self.req.code}"
                )

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
                        self.req.add_auth(pwd)
                    else:
                        self.fail(self._("Authorization required"))
            else:
                break

        self.check_download()

    def check_download(self):
        errmsg = self.scan_download(
            {
                "Html error": re.compile(
                    r"\A(?:\s*<.+>)?((?:[\w\s]*(?:[Ee]rror|ERROR)\s*\:?)?\s*\d{3})(?:\Z|\s+)"
                ),
                "Html file": re.compile(r"\A\s*<!DOCTYPE html"),
                "Request error": re.compile(
                    r"([Aa]n error occured while processing your request)"
                ),
            }
        )

        if not errmsg:
            return

        try:
            errmsg += " | " + self.last_check.group(1).strip()

        except Exception:
            pass

        self.log_warning(
            self._("Check result: ") + errmsg, self._("Waiting 1 minute and retry")
        )
        self.retry(3, 60, errmsg)
