# -*- coding: utf-8 -*-

from ..base.simple_downloader import SimpleDownloader


class DropboxCom(SimpleDownloader):
    __name__ = "DropboxCom"
    __type__ = "downloader"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?dropbox\.com/.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Dropbox.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]

    NAME_PATTERN = r"<title>Dropbox - (?P<N>.+?)<"
    SIZE_PATTERN = r"&nbsp;&middot;&nbsp; (?P<S>[\d.,]+) (?P<U>[\w^_]+)"

    LINK_PATTERN = r'<a href="(?P<url>[^"]+?)" id="default_content_download_button" class="freshbutton-blue">'

    OFFLINE_PATTERN = r"<title>Dropbox - (404|Shared link error)<"

    COOKIES = [("dropbox.com", "lang", "en")]

    def setup(self):
        self.multi_dl = True
        self.chunk_limit = 1
        self.resume_download = True

    def handle_free(self, pyfile):
        self.download(pyfile.url, get={"dl": "1"})
