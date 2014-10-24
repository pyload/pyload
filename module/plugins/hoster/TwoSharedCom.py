# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class TwoSharedCom(SimpleHoster):
    __name__ = "TwoSharedCom"
    __type__ = "hoster"
    __version__ = "0.12"

    __pattern__ = r'http://(?:www\.)?2shared\.com/(account/)?(download|get|file|document|photo|video|audio)/.*'

    __description__ = """2Shared.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    FILE_NAME_PATTERN = r'<h1>(?P<N>.*)</h1>'
    FILE_SIZE_PATTERN = r'<span class="dtitle">File size:</span>\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'The file link that you requested is not valid\.|This file was deleted\.'

    LINK_PATTERN = r'window.location =\'(.+?)\';'


    def setup(self):
        self.resumeDownload = self.multiDL = True


    def handleFree(self):
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error('Download link')

        link = m.group(1)
        self.download(link)


getInfo = create_getInfo(TwoSharedCom)
