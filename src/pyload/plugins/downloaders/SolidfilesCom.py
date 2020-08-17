# -*- coding: utf-8 -*-


from ..base.simple_downloader import SimpleDownloader

#
# Test links:
#   http://www.solidfiles.com/d/609cdb4b1b


class SolidfilesCom(SimpleDownloader):
    __name__ = "SolidfilesCom"
    __type__ = "downloader"
    __version__ = "0.08"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?solidfiles\.com\/d/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Solidfiles.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("sraedler", "simon.raedler@yahoo.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    NAME_PATTERN = r'<i class="icon filetype-icon.+?</i>\s*<h1>\s*(?P<N>.+?)\s*</h1>'
    SIZE_PATTERN = r'copy-text="viewer\.node\.viewUrl"></copy-button>\s*(?P<S>[\d.,]+) (?P<U>[\w_^]+)'
    OFFLINE_PATTERN = r"<h1>404"

    LINK_FREE_PATTERN = r'<a href="(https?://.*\.solidfilesusercontent\.com/.+?)"'

    def setup(self):
        self.multi_dl = True
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        action, inputs = self.parse_html_form('action="/v/')
        if not action or not inputs:
            self.error(self._("Free download form not found"))

        self.data = self.load(self.fixurl(action), post=inputs)

        super().handle_free(pyfile)
