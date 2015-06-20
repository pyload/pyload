# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FourSharedCom(SimpleHoster):
    __name__    = "FourSharedCom"
    __type__    = "hoster"
    __version__ = "0.31"

    __pattern__ = r'https?://(?:www\.)?4shared(\-china)?\.com/(account/)?(download|get|file|document|photo|video|audio|mp3|office|rar|zip|archive|music)/.+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """4Shared.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("jeix", "jeix@hasnomail.de"),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'<meta name="title" content="(?P<N>.+?)"'
    SIZE_PATTERN = r'<span title="Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)">'
    OFFLINE_PATTERN = r'The file link that you requested is not valid\.|This file was deleted.'

    NAME_REPLACEMENTS = [(r"&#(\d+).", lambda m: unichr(int(m.group(1))))]
    SIZE_REPLACEMENTS = [(",", "")]

    DIRECT_LINK   = False
    LOGIN_ACCOUNT = True

    LINK_FREE_PATTERN = r'name="d3link" value="(.*?)"'
    LINK_BTN_PATTERN  = r'id="btnLink" href="(.*?)"'

    ID_PATTERN = r'name="d3fid" value="(.*?)"'


    def handleFree(self, pyfile):
        m = re.search(self.LINK_BTN_PATTERN, self.html)
        if m:
            link = m.group(1)
        else:
            link = re.sub(r'/(download|get|file|document|photo|video|audio)/', r'/get/', pyfile.url)

        self.html = self.load(link)

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("Download link"))

        self.link = m.group(1)

        try:
            m = re.search(self.ID_PATTERN, self.html)
            res = self.load('http://www.4shared.com/web/d2/getFreeDownloadLimitInfo?fileId=%s' % m.group(1))
            self.logDebug(res)
        except Exception:
            pass

        self.wait(20)


getInfo = create_getInfo(FourSharedCom)
