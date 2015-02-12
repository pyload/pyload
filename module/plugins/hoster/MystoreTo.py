# -*- coding: utf-8 -*-
# Testlink: http://mystore.to/dl/mxcA50jKfP

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class MystoreTo(SimpleHoster):
    __name__    = "MystoreTo"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?mystore.to/dl/.+'

    __description__ = """Mystore.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "")]


    NAME_PATTERN    = r'<h1>(?P<N>.*?)</h1>'
    SIZE_PATTERN    = r'FILESIZE: (?P<S>[\d\.,]+) (?P<U>[\w^_]+)<'
    OFFLINE_PATTERN = r'the file is no longer available'


    def setup(self):
        self.chunkLimit = 1
        self.resumeDownload = self.multiDL = True


    def handleFree(self, pyfile):
        try:
            fid = re.search(r'wert="(.*?)"', self.html).group(1)
        except AttributeError:
            self.error(_("File-ID not found"))
            
        self.link = self.load("http://mystore.to/api/download",
                              post={"FID":fid})

getInfo = create_getInfo(MystoreTo)
