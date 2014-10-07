# -*- coding: utf-8 -*-
#
# Test links:
# http://speedy.sh/ep2qY/Zapp-Brannigan.jpg

import re

from urlparse import urljoin

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class SpeedyshareCom(SimpleHoster):
    __name__ = "SpeedyshareCom"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r"https?://(?:www\.)?(speedyshare\.com|speedy\.sh)/\w+"

    __description__ = """Speedyshare.com hoster plugin"""
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]


    FILE_NAME_PATTERN = r'class=downloadfilename>(?P<N>.*)</span></td>'
    FILE_SIZE_PATTERN = r'class=sizetagtext>(?P<S>.*) (?P<U>[kKmM]?[iI]?[bB]?)</div>'

    FILE_OFFLINE_PATTERN = r'class=downloadfilenamenotfound>.*</span>'

    LINK_PATTERN = r'<a href=\'(.*)\'><img src=/gf/slowdownload.png alt=\'Slow Download\' border=0'


    def setup(self):
        self.multiDL = False
        self.chunkLimit = 1


    def handleFree(self):
        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.parseError("Download link not found")

        dl_link = urljoin("http://www.speedyshare.com", m.group(1))
        self.download(dl_link, disposition=True)

        check = self.checkDownload({'html': re.compile("html")})
        if check == "html":
            self.parseError("Downloaded file is an html file")


getInfo = create_getInfo(SpeedyshareCom)
