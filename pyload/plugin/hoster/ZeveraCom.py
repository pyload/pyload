# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from pyload.plugin.internal.MultiHoster import MultiHoster


class ZeveraCom(MultiHoster):
    __name__    = "ZeveraCom"
    __type__    = "hoster"
    __version__ = "0.29"

    __pattern__ = r'https?://(?:www\.)zevera\.com/(getFiles\.ashx|Members/download\.ashx)\?.*ourl=.+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Zevera.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def handlePremium(self, pyfile):
        self.link = "https://%s/getFiles.ashx?ourl=%s" % (self.account.HOSTER_DOMAIN, pyfile.url)


    def checkFile(self, rules={}):
        if self.checkDownload({"error": 'action="ErrorDownload.aspx'}):
            self.fail(_("Error response received"))

        return super(ZeveraCom, self).checkFile(rules)
