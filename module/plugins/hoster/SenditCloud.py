# -*- coding: utf-8 -*-

from ..internal.SimpleHoster import SimpleHoster


class SenditCloud(SimpleHoster):
    __name__ = "SenditCloud"
    __type__ = "hoster"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?sendit\.cloud/\w+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Sendit.cloud hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'<header class="widget-header ">.+>\s*(.+?)\s*</header>'
    SIZE_PATTERN = r'<b>Download</b> <font color="#FFFFFF">\((?P<S>[\d.,]+) (?P<U>[\w_^]+)\)<'

    OFFLINE_PATTERN = r'The file you are trying to download is no longer available'

    def setup(self):
        self.multiDL = True
        self.resume_download = False

    def handle_free(self, pyfile):
        url, inputs = self.parse_html_form('name="F1"')
        if inputs is not None:
            self.download(pyfile.url, post=inputs)