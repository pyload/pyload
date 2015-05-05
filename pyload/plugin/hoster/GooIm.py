# -*- coding: utf-8 -*-
#
# Test links:
#   https://goo.im/devs/liquidsmooth/3.x/codina/Nightly/LS-KK-v3.2-2014-08-01-codina.zip

from pyload.plugin.internal.SimpleHoster import SimpleHoster


class GooIm(SimpleHoster):
    __name    = "GooIm"
    __type    = "hoster"
    __version = "0.04"

    __pattern = r'https?://(?:www\.)?goo\.im/.+'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Goo.im hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN = r'You will be redirected to .*(?P<N>[^/ ]+)  in'
    OFFLINE_PATTERN = r'The file you requested was not found'


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True


    def handle_free(self, pyfile):
        self.wait(10)
        self.link = pyfile.url
