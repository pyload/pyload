# -*- coding: utf-8 -*-
#
# Test links:
# https://goo.im/devs/liquidsmooth/3.x/codina/Nightly/LS-KK-v3.2-2014-08-01-codina.zip

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class GooIm(SimpleHoster):
    __name__    = "GooIm"
    __type__    = "hoster"
    __version__ = "0.04"

    __pattern__ = r'https?://(?:www\.)?goo\.im/.+'

    __description__ = """Goo.im hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN = r'You will be redirected to .*(?P<N>[^/ ]+)  in'
    OFFLINE_PATTERN = r'The file you requested was not found'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True


    def handleFree(self, pyfile):
        self.wait(10)
        self.download(pyfile.url, cookies=True)


getInfo = create_getInfo(GooIm)
