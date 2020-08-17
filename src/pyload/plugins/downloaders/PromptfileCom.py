# -*- coding: utf-8 -*-

import re

from ..base.simple_downloader import SimpleDownloader


class PromptfileCom(SimpleDownloader):
    __name__ = "PromptfileCom"
    __type__ = "downloader"
    __version__ = "0.19"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?promptfile\.com/"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Promptfile.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("igel", "igelkun@myopera.com"), ("ondrej", "git@ondrej.it")]

    INFO_PATTERN = r'<span style=".+?" title=".+?">(?P<N>.*?) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</span>'
    OFFLINE_PATTERN = r'<span style=".+?" title="File Not Found">File Not Found</span>'

    CHASH_PATTERN = r'input.+"([a-z\d]{10,})".+"([a-z\d]{10,})"'
    MODIFY_PATTERN = r'\$\("#chash"\)\.val\("(.+)"\+\$\("#chash"\)'
    LINK_FREE_PATTERN = r'<a href="(http://www\.promptfile\.com/file/[^"]+)'

    def handle_free(self, pyfile):
        #: STAGE 1: get link to continue
        m = re.search(self.CHASH_PATTERN, self.data)
        if m is None:
            self.error(self._("CHASH_PATTERN not found"))

        mod = re.search(self.MODIFY_PATTERN, self.data)
        payload = {m.group(1): mod.group(1) + m.group(2)}

        self.log_debug(f"Read chash: {payload}")

        #: Continue to stage2
        self.data = self.load(pyfile.url, post=payload)

        #: STAGE 2: get the direct link
        return super().handle_free(pyfile)
