# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FourSharedCom(SimpleHoster):
    __name__ = "FourSharedCom"
    __type__ = "hoster"
    __version__ = "0.29"

    __pattern__ = r'https?://(?:www\.)?4shared(\-china)?\.com/(account/)?(download|get|file|document|photo|video|audio|mp3|office|rar|zip|archive|music)/.+?/.*'

    __description__ = """4Shared.com hoster plugin"""
    __author_name__ = ("jeix", "zoidberg")
    __author_mail__ = ("jeix@hasnomail.de", "zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<meta name="title" content="(?P<N>.+?)"'
    FILE_SIZE_PATTERN = r'<span title="Size: (?P<S>[0-9,.]+) (?P<U>[kKMG])i?B">'
    OFFLINE_PATTERN = r'The file link that you requested is not valid\.|This file was deleted.'

    FILE_NAME_REPLACEMENTS = [(r"&#(\d+).", lambda m: unichr(int(m.group(1))))]
    FILE_SIZE_REPLACEMENTS = [(",", "")]

    DOWNLOAD_URL_PATTERN = r'name="d3link" value="(.*?)"'
    DOWNLOAD_BUTTON_PATTERN = r'id="btnLink" href="(.*?)"'
    FID_PATTERN = r'name="d3fid" value="(.*?)"'


    def handleFree(self):
        if not self.account:
            self.fail("User not logged in")

        m = re.search(self.DOWNLOAD_BUTTON_PATTERN, self.html)
        if m:
            link = m.group(1)
        else:
            link = re.sub(r'/(download|get|file|document|photo|video|audio)/', r'/get/', self.pyfile.url)

        self.html = self.load(link)

        m = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
        if m is None:
            self.parseError('Download link')
        link = m.group(1)

        try:
            m = re.search(self.FID_PATTERN, self.html)
            response = self.load('http://www.4shared.com/web/d2/getFreeDownloadLimitInfo?fileId=%s' % m.group(1))
            self.logDebug(response)
        except:
            pass

        self.wait(20)
        self.download(link)


getInfo = create_getInfo(FourSharedCom)
