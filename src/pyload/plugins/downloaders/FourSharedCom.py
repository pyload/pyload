# -*- coding: utf-8 -*-

import re

from ..base.simple_downloader import SimpleDownloader


class FourSharedCom(SimpleDownloader):
    __name__ = "FourSharedCom"
    __type__ = "downloader"
    __version__ = "0.37"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?4shared(-china)?\.com/(account/)?(download|get|file|document|photo|video|audio|mp3|office|rar|zip|archive|music)/.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """4Shared.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("jeix", "jeix@hasnomail.de"), ("zoidberg", "zoidberg@mujmail.cz")]

    NAME_PATTERN = r'<meta name="title" content="(?P<N>.+?)"'
    SIZE_PATTERN = r'<span title="Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)">'
    OFFLINE_PATTERN = (
        r"The file link that you requested is not valid\.|This file was deleted."
    )

    NAME_REPLACEMENTS = [(r"&#(\d+).", lambda m: chr(int(m.group(1))))]
    SIZE_REPLACEMENTS = [(",", "")]

    DIRECT_LINK = False
    LOGIN_ACCOUNT = True

    LINK_FREE_PATTERN = r'name="d3link" value="(.*?)"'
    LINK_BTN_PATTERN = r'id="btnLink" href="(.*?)"'

    ID_PATTERN = r'name="d3fid" value="(.*?)"'

    def handle_free(self, pyfile):
        m = re.search(self.LINK_BTN_PATTERN, self.data)
        if m is not None:
            link = m.group(1)
        else:
            link = re.sub(
                r"/(download|get|file|document|photo|video|audio)/",
                r"/get/",
                pyfile.url,
            )

        self.data = self.load(link)

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            return

        self.link = m.group(1)

        try:
            m = re.search(self.ID_PATTERN, self.data)
            id = m.group(1)
            res = self.load(
                f"http://www.4shared.com/web/d2/getFreeDownloadLimitInfo?fileId={id}"
            )
            self.log_debug(res)

        except Exception:
            pass

        self.wait(20)
