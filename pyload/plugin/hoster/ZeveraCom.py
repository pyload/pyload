# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from pyload.plugin.internal.MultiHoster import MultiHoster


class ZeveraCom(MultiHoster):
    __name    = "ZeveraCom"
    __type    = "hoster"
    __version = "0.28"

    __pattern = r'https?://(?:www\.)zevera\.com/(getFiles\.ashx|Members/download\.ashx)\?.*ourl=.+'

    __description = """Zevera.com multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def handlePremium(self, pyfile):
        self.link = "https://%s/getFiles.ashx?ourl=%s" % (self.account.HOSTER_DOMAIN, pyfile.url)


    def checkFile(self):
        if self.checkDownload({"error": 'action="ErrorDownload.aspx'}):
            self.fail(_("Error response received"))

        return super(ZeveraCom, self).checkFile()
