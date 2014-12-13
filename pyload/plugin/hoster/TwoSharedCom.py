# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster, create_getInfo


class TwoSharedCom(SimpleHoster):
    __name    = "TwoSharedCom"
    __type    = "hoster"
    __version = "0.12"

    __pattern = r'http://(?:www\.)?2shared\.com/(account/)?(download|get|file|document|photo|video|audio)/.*'

    __description = """2Shared.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    NAME_PATTERN = r'<h1>(?P<N>.*)</h1>'
    SIZE_PATTERN = r'<span class="dtitle">File size:</span>\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'The file link that you requested is not valid\.|This file was deleted\.'

    LINK_PATTERN = r'window.location =\'(.+?)\';'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True


    def handleFree(self):
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error(_("Download link"))

        link = m.group(1)
        self.download(link)


getInfo = create_getInfo(TwoSharedCom)
