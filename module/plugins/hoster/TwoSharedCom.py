# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class TwoSharedCom(SimpleHoster):
    __name__ = "TwoSharedCom"
    __type__ = "hoster"
    __version__ = "0.11"

    __pattern__ = r'http://(?:www\.)?2shared.com/(account/)?(download|get|file|document|photo|video|audio)/.*'

    __description__ = """2Shared.com hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_NAME_PATTERN = r'<h1>(?P<N>.*)</h1>'
    FILE_SIZE_PATTERN = r'<span class="dtitle">File size:</span>\s*(?P<S>[0-9,.]+) (?P<U>[kKMG])i?B'
    OFFLINE_PATTERN = r'The file link that you requested is not valid\.|This file was deleted\.'

    LINK_PATTERN = r"window.location ='([^']+)';"


    def setup(self):
        self.resumeDownload = self.multiDL = True

    def handleFree(self):
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.parseError('Download link')
        link = m.group(1)
        self.logDebug("Download URL %s" % link)

        self.download(link)


getInfo = create_getInfo(TwoSharedCom)
