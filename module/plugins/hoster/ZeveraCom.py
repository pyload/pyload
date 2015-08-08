# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class ZeveraCom(MultiHoster):
    __name__    = "ZeveraCom"
    __type__    = "hoster"
    __version__ = "0.32"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)zevera\.com/(getFiles\.ashx|Members/download\.ashx)\?.*ourl=.+'
    __config__  = [("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Zevera.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    FILE_ERRORS = [("Error", r'action="ErrorDownload.aspx')]


    def handle_premium(self, pyfile):
        self.link = "https://%s/getFiles.ashx?ourl=%s" % (self.account.HOSTER_DOMAIN, pyfile.url)


getInfo = create_getInfo(ZeveraCom)
