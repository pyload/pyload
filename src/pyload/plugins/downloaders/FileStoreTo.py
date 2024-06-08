# -*- coding: utf-8 -*-
import random
import re

from pyload.core.network.http.exceptions import BadHeader

from ..base.simple_downloader import SimpleDownloader


class FileStoreTo(SimpleDownloader):
    __name__ = "FileStoreTo"
    __type__ = "downloader"
    __version__ = "0.17"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?filestore\.to/\?d=(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("freeslot_wait", "int", "Delay to wait for free slot (seconds)", 600),
        ("freeslot_attempts", "int", "Number of retries to wait for free slot", 15),
        ("beadheader_retry", "bool", "Retry download on HTTP Header 503", True)
    ]

    __description__ = """FileStore.to downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    NAME_PATTERN = r'<div class="file">(?P<N>.+?)</div>'
    SIZE_PATTERN = r'<div class="size">(?P<S>[\d.,]+) (?P<U>[\w^_]+)</div>'

    OFFLINE_PATTERN = r">(?:Download-Datei wurde nicht gefunden|Datei nicht gefunden)<"
    TEMP_OFFLINE_PATTERN = r">Der Download ist nicht bereit !<"
    NO_FREESLOTS_PATTERN = r">Leider sind aktuell keine freien Downloadslots für Freeuser verfügbar<"

    WAIT_PATTERN = r'data-wait="(\d+?)"'
    LINK_PATTERN = r'klicke <a href="(.+?)">hier<'

    URL_REPLACEMENTS = [("http://", "https://")]

    def setup(self):
        self.resume_download = True
        self.multi_dl = True

    def process(self, pyfile):
        try:
            return super().process(pyfile)

        except BadHeader as exc:
            self.log_debug(f"FileStore.to httpcode: {exc.code}")
            if exc.code == 503 and self.config.get("beadheader_retry", True):
                rand_delay = random.randrange(0, 6) * 5
                self.log_warning(self._("Temporary server error, retrying..."))
                self.retry(10, 10 + rand_delay)

            else:
                raise

    def handle_free(self, pyfile):
        self.data = self.load(pyfile.url, post={"Aktion": "Download"})

        self.check_errors()

        m = re.search(r'name="DID" value="(.+?)"', self.data)
        if m is None:
            self.fail(self._("DID pattern not found"))

        self.data = self.load(
            pyfile.url, post={"DID": m.group(1), "Aktion": "Downloading"}
        )

        self.check_errors()

        m = re.search(self.LINK_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)

    def handle_premium(self, pyfile):
        m = re.search(r'name="DID" value="(.+?)"', self.data)
        if m is None:
            self.fail(self._("DID pattern not found"))

        self.data = self.load(
            pyfile.url, post={"DID": m.group(1), "Aktion": "Downloading"}
        )

        self.check_errors()

        m = re.search(self.LINK_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)

    def check_errors(self, data=None):
        if re.search(self.NO_FREESLOTS_PATTERN, self.data) is not None:
            self.log_warning(self._("No free slot available"))
            freeslot_wait = self.config.get("freeslot_wait", 600)
            freeslot_attempts = self.config.get("freeslot_attempts", 15)
            self.retry(attempts=freeslot_attempts, wait=freeslot_wait)

        else:
            super(FileStoreTo, self).check_errors(data=data)

