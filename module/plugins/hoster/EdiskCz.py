# -*- coding: utf-8 -*-

import re

from ..internal.SimpleHoster import SimpleHoster


class EdiskCz(SimpleHoster):
    __name__ = "EdiskCz"
    __type__ = "hoster"
    __version__ = "0.28"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?edisk\.(cz|sk|eu)/(stahni|sk/stahni|en/download)/.+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Edisk.cz hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    INFO_PATTERN = r'<span class="fl" title="(?P<N>.+?)">\s*.*?\((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</h1></span>'
    OFFLINE_PATTERN = r'<h3>This file does not exist due to one of the following:</h3><ul><li>'

    ACTION_PATTERN = r'/en/download/(\d+/.*\.html)'
    LINK_FREE_PATTERN = r'http://.*edisk\.cz.*\.html'

    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
        url = re.sub("/(stahni|sk/stahni)/", "/en/download/", pyfile.url)

        self.log_debug("URL:" + url)

        m = re.search(self.ACTION_PATTERN, url)
        if m is None:
            self.error(_("ACTION_PATTERN not found"))
        action = m.group(1)

        self.data = self.load(url)
        self.get_fileInfo()

        self.data = self.load(
            re.sub(
                "/en/download/",
                "/en/download-slow/",
                url))

        url = self.load(re.sub("/en/download/", "/x-download/", url), post={
            'action': action
        })

        if not re.match(self.LINK_FREE_PATTERN, url):
            self.fail(_("Unexpected server response"))

        self.link = url
