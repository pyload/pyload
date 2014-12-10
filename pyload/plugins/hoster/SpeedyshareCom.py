# -*- coding: utf-8 -*-
#
# Test links:
# http://speedy.sh/ep2qY/Zapp-Brannigan.jpg

import re

from urlparse import urljoin

from pyload.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class SpeedyshareCom(SimpleHoster):
    __name    = "SpeedyshareCom"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'https?://(?:www\.)?(speedyshare\.com|speedy\.sh)/\w+'

    __description = """Speedyshare.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN = r'class=downloadfilename>(?P<N>.*)</span></td>'
    SIZE_PATTERN = r'class=sizetagtext>(?P<S>.*) (?P<U>[kKmM]?[iI]?[bB]?)</div>'

    OFFLINE_PATTERN = r'class=downloadfilenamenotfound>.*</span>'

    LINK_PATTERN = r'<a href=\'(.*)\'><img src=/gf/slowdownload\.png alt=\'Slow Download\' border=0'


    def setup(self):
        self.multiDL = False
        self.chunkLimit = 1


    def handleFree(self):
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error(_("Download link not found"))

        dl_link = urljoin("http://www.speedyshare.com", m.group(1))
        self.download(dl_link, disposition=True)

        check = self.checkDownload({'html': re.compile("html")})
        if check == "html":
            self.error(_("Downloaded file is an html page"))


getInfo = create_getInfo(SpeedyshareCom)
