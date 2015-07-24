# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class PromptfileCom(SimpleHoster):
    __name__    = "PromptfileCom"
    __type__    = "hoster"
    __version__ = "0.14"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?promptfile\.com/'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Promptfile.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("igel", "igelkun@myopera.com")]


    INFO_PATTERN    = r'<span style=".+?" title=".+?">(?P<N>.*?) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</span>'
    OFFLINE_PATTERN = r'<span style=".+?" title="File Not Found">File Not Found</span>'

    CHASH_PATTERN     = r'<input type="hidden" name="chash" value="(.+?)" />'
    LINK_FREE_PATTERN = r'<a href=\"(.+)\" target=\"_blank\" class=\"view_dl_link\">Download File</a>'


    def handle_free(self, pyfile):
        #: STAGE 1: get link to continue
        m = re.search(self.CHASH_PATTERN, self.html)
        if m is None:
            self.error(_("CHASH_PATTERN not found"))

        chash = m.group(1)
        self.log_debug("Read chash %s" % chash)

        #: Continue to stage2
        self.html = self.load(pyfile.url, post={'chash': chash})

        #: STAGE 2: get the direct link
        return super(PromptfileCom, self).handle_free(pyfile)


getInfo = create_getInfo(PromptfileCom)
