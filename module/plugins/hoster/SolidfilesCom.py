# -*- coding: utf-8 -*-
#
# Test links:
#   http://www.solidfiles.com/d/609cdb4b1b

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class SolidfilesCom(SimpleHoster):
    __name__    = "SolidfilesCom"
    __type__    = "hoster"
    __version__ = "0.03"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?solidfiles\.com\/d/\w+'

    __description__ = """Solidfiles.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("sraedler", "simon.raedler@yahoo.de")]


    NAME_PATTERN    = r'<h1 title="(?P<N>.+?)"'
    SIZE_PATTERN    = r'<p class="meta">(?P<S>[\d.,]+) (?P<U>[\w_^]+)'
    OFFLINE_PATTERN = r'<h1>404'

    LINK_FREE_PATTERN = r'id="ddl-text" href="(.+?)"'


    def setup(self):
        self.multiDL    = True
        self.chunk_limit = 1


getInfo = create_getInfo(SolidfilesCom)
