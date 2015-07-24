# -*- coding: utf-8 -*-
#
# Test link:
#   http://mystore.to/dl/mxcA50jKfP

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class MystoreTo(SimpleHoster):
    __name__    = "MystoreTo"
    __type__    = "hoster"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?mystore\.to/dl/.+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Mystore.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "")]


    NAME_PATTERN    = r'<h1>(?P<N>.+?)<'
    SIZE_PATTERN    = r'FILESIZE: (?P<S>[\d\.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>file not found<'


    def setup(self):
        self.chunk_limit     = 1
        self.resume_download = True
        self.multiDL        = True


    def handle_free(self, pyfile):
        try:
            fid = re.search(r'wert="(.+?)"', self.html).group(1)

        except AttributeError:
            self.error(_("File-ID not found"))

        self.link = self.load("http://mystore.to/api/download",
                              post={'FID': fid})


getInfo = create_getInfo(MystoreTo)
