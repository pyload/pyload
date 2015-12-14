# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster


class PromptfileCom(SimpleHoster):
    __name__    = "PromptfileCom"
    __type__    = "hoster"
    __version__ = "0.17"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?promptfile\.com/'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Promptfile.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("igel", "igelkun@myopera.com")]


    INFO_PATTERN    = r'<span style=".+?" title=".+?">(?P<N>.*?) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</span>'
    OFFLINE_PATTERN = r'<span style=".+?" title="File Not Found">File Not Found</span>'

    CHASH_PATTERN     = r'<input type="hidden" name="chash" value="(.+?)" />'
    LINK_FREE_PATTERN = r'<a href=\"(.+)\" target=\"_blank\" class=\"view_dl_link\">Download File</a>'


    def handle_free(self, pyfile):
        #: STAGE 1: get link to continue
        m = re.search(self.CHASH_PATTERN, self.data)
        if m is None:
            self.error(_("CHASH_PATTERN not found"))

        chash = m.group(1)
        self.log_debug("Read chash %s" % chash)

        #: Continue to stage2
        self.data = self.load(pyfile.url, post={'chash': chash})

        #: STAGE 2: get the direct link
        return super(PromptfileCom, self).handle_free(pyfile)
