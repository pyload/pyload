# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class PromptfileCom(SimpleHoster):
    __name    = "PromptfileCom"
    __type    = "hoster"
    __version = "0.13"

    __pattern = r'https?://(?:www\.)?promptfile\.com/'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Promptfile.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("igel", "igelkun@myopera.com")]


    INFO_PATTERN = r'<span style=".+?" title=".+?">(?P<N>.*?) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</span>'
    OFFLINE_PATTERN = r'<span style=".+?" title="File Not Found">File Not Found</span>'

    CHASH_PATTERN = r'<input type="hidden" name="chash" value="(.+?)" />'
    LINK_FREE_PATTERN = r'<a href=\"(.+)\" target=\"_blank\" class=\"view_dl_link\">Download File</a>'


    def handleFree(self, pyfile):
        # STAGE 1: get link to continue
        m = re.search(self.CHASH_PATTERN, self.html)
        if m is None:
            self.error(_("CHASH_PATTERN not found"))
        chash = m.group(1)
        self.logDebug("Read chash %s" % chash)
        # continue to stage2
        self.html = self.load(pyfile.url, decode=True, post={'chash': chash})

        # STAGE 2: get the direct link
        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_FREE_PATTERN not found"))

        self.link = m.group(1)
