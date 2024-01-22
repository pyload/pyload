# -*- coding: utf-8 -*-

import fnmatch
import re
import urllib.parse

from pyload.core.network.http.exceptions import BadHeader

from ..base.downloader import BaseDownloader


class Http(BaseDownloader):
    __name__ = "Http"
    __type__ = "downloader"
    __version__ = "0.15"
    __status__ = "testing"

    __pattern__ = r"(?:jd|pys?)://.+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Download simple http link"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    def setup(self):
        self.chunk_limit = -1
        self.resume_download = True

    def load_account(self):
        class_name = self.classname
        self.__class__.__name__ = "Http"
        super().load_account()
        self.__class__.__name__ = class_name

    def process(self, pyfile):
        url = re.sub(r"^(jd|py)", "http", pyfile.url)

        netloc = urllib.parse.urlparse(url).netloc
        try:
            auth, netloc = netloc.split('@', 2)
        except ValueError:
            auth = None

        if auth is None:
            password = self.get_password()
            if ":" in password:
                auth = password
                self.log_debug(f"Logging on to {netloc} using credentials specified in the package password")

            else:
                if self.account:
                    logins = dict((x['login'], x['password'])
                                  for x in self.account.get_all_accounts())
                else:
                    logins = {}

                for pattern, auth in logins.items():
                    if fnmatch.fnmatch(netloc, pattern):
                        self.log_debug(f"Logging on to {netloc} using the account plugin")
                        break
                else:
                    auth = None

            if auth is not None:
                self.req.add_auth(auth)

        else:
            self.log_debug(f"Logging on to {netloc} using credentials specified in the URL")

        try:
            self.download(url, ref=False, disposition=True)

        except BadHeader as exc:
            if exc.code == 401:
                self.fail(self._("Unauthorized"))

            else:
                raise

        if self.req.code in (404, 410):
            self.offline()

        self.check_download()

    def check_download(self):
        errmsg = self.scan_download(
            {
                "Html error": re.compile(
                    rb"\A(?:\s*<.+>)?((?:[\w\s]*(?:[Ee]rror|ERROR)\s*\:?)?\s*\d{3})(?:\Z|\s+)"
                ),
                "Html file": re.compile(rb"\A\s*<!DOCTYPE html"),
                "Request error": re.compile(
                    rb"([Aa]n error occured while processing your request)"
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
