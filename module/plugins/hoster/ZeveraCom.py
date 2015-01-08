# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class ZeveraCom(MultiHoster):
    __name__    = "ZeveraCom"
    __type__    = "hoster"
    __version__ = "0.26"

    __pattern__ = r'https?://(?:www\.)zevera\.com/(getFiles\.ashx|Members/download\.ashx)\?.*ourl=.+'

    __description__ = """Zevera.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def handlePremium(self, pyfile):
        html = self.account.api_response(self.req, cmd="checklink", olink=pyfile.url)
        if "Alive" in html:
            header    = self.account.api_response(self.req, just_header=True, cmd="generatedownloaddirect", olink=pyfile.url)
            self.link = self.directLink(header['location'])
        else:
            self.fail(re.search(r'Error: (.+)', html).group(1))


    def checkFile(self):
        if self.checkDownload({"error": 'action="ErrorDownload.aspx'}):
            self.fail(_("Error response received"))

        return super(ZeveraCom, self).checkFile()


getInfo = create_getInfo(ZeveraCom)
