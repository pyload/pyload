# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class PromptfileCom(SimpleHoster):
    __name__ = "PromptfileCom"
    __type__ = "hoster"
    __version__ = "0.1"

    __pattern__ = r'https?://(?:www\.)?promptfile\.com/'

    __description__ = """Promptfile.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("igel", "igelkun@myopera.com")]


    FILE_INFO_PATTERN = r'<span style="[^"]*" title="[^"]*">(?P<N>.*?) \((?P<S>[\d.,]+) (?P<U>[\w^_]+)\)</span>'
    OFFLINE_PATTERN = r'<span style="[^"]*" title="File Not Found">File Not Found</span>'

    CHASH_PATTERN = r'<input type="hidden" name="chash" value="([^"]*)" />'
    LINK_PATTERN = r'clip: {\s*url: \'(https?://(?:www\.)promptfile[^\']*)\','


    def handleFree(self):
        # STAGE 1: get link to continue
        m = re.search(self.CHASH_PATTERN, self.html)
        if m is None:
            self.parseError("Unable to detect chash")
        chash = m.group(1)
        self.logDebug("Read chash %s" % chash)
        # continue to stage2
        self.html = self.load(self.pyfile.url, decode=True, post={'chash': chash})

        # STAGE 2: get the direct link
        m = re.search(self.LINK_PATTERN, self.html, re.MULTILINE | re.DOTALL)
        if m is None:
            self.parseError("Unable to detect direct link")
        direct = m.group(1)
        self.logDebug("Found direct link: " + direct)
        self.download(direct, disposition=True)


getInfo = create_getInfo(PromptfileCom)
